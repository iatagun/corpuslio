"""Views for corpus management."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

from .models import Document, ProcessingTask, Analysis, Tag, Content, CorpusMetadata
from .forms import DocumentUploadForm
from .tasks import process_document_task
from .services import CorpusService
from .services import CorpusService
from .collections import Collection
import os
from django.contrib.auth.decorators import user_passes_test, login_required

def rate_limit_exceeded(request, exception=None):
    """Custom 429 error handler for rate limiting."""
    return render(request, 'corpus/429.html', status=429)


def csrf_failure(request, reason=""):
    """Custom 403 CSRF error handler."""
    context = {
        'message': 'CSRF verification failed. Request aborted.',
        'reason': reason,
    }
    return render(request, 'corpus/403_csrf.html', context, status=403)


def is_academician(user):
    """Check if user has Academician or Developer access."""
    return user.is_authenticated and (
        user.is_superuser or 
        user.groups.filter(name__in=['Academician', 'Developer']).exists()
    )

def is_developer(user):
    return user.is_authenticated and (
        user.is_superuser or 
        user.groups.filter(name='Developer').exists()
    )


def home_view(request):
    """Corpus Query Platform landing page."""
    from .models import Token, Sentence, CorpusMetadata
    
    # Corpus statistics
    total_corpora = CorpusMetadata.objects.count()
    total_documents = Document.objects.count()
    total_tokens = Token.objects.count()
    total_sentences = Sentence.objects.count()
    
    # Recent corpus uploads
    recent_corpora = CorpusMetadata.objects.select_related('document').all().order_by('-imported_at')[:4]
    
    total_collections = Collection.objects.count()
    
    # Popular tags (top 10 by document count)
    from django.db.models import Count
    popular_tags = Tag.objects.annotate(
        doc_count=Count('documents')
    ).filter(doc_count__gt=0).order_by('-doc_count')[:10]
    
    context = {
        'total_corpora': total_corpora,
        'total_documents': total_documents,
        'total_tokens': total_tokens,
        'total_sentences': total_sentences,
        'total_collections': total_collections,
        'recent_corpora': recent_corpora,
        'popular_tags': popular_tags,
        'active_tab': 'home'
    }
    return render(request, 'corpus/home.html', context)


@ensure_csrf_cookie
@ratelimit(key='user_or_ip', rate='1000/d', method='GET')
def library_view(request):
    """Display all corpus files with metadata filtering.

    Shows CorpusMetadata entries with linguistic statistics.
    Anonymous users see limited view.
    
    Rate limit: 1000 requests per day per user or IP address.
    """
    # Bypass rate limit for superusers
    if request.user.is_authenticated and request.user.is_superuser:
        request.limited = False
    
    corpora = CorpusMetadata.objects.select_related('document').all().order_by('-imported_at')
    
    # Metadata filters (JSONField access)
    author_filter = request.GET.get('author')
    genre_filter = request.GET.get('genre')
    date_filter = request.GET.get('date')
    search_query = request.GET.get('q')
    format_filter = request.GET.get('format')
    
    if author_filter:
        corpora = corpora.filter(global_metadata__author__icontains=author_filter)
    
    if genre_filter:
        corpora = corpora.filter(global_metadata__genre__icontains=genre_filter)
    
    if date_filter:
        corpora = corpora.filter(global_metadata__date__icontains=date_filter)
    
    if format_filter:
        corpora = corpora.filter(source_format=format_filter)
    
    if search_query:
        from django.db.models import Q
        corpora = corpora.filter(
            Q(original_filename__icontains=search_query) |
            Q(global_metadata__author__icontains=search_query) |
            Q(global_metadata__genre__icontains=search_query)
        )
    
    # Anonymous users see limited results
    is_limited_public_view = not request.user.is_authenticated
    if is_limited_public_view:
        # No specific limit for corpus metadata (all are "processed")
        pass

    # Pagination (Infinite scroll)
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    page_size = 12 if is_limited_public_view else 20
    paginator = Paginator(corpora, page_size)
    
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Check if this is an AJAX request for infinite scroll
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return JSON data for AJAX infinite scroll
        corpora_data = []
        for corpus in page_obj:
            corpora_data.append({
                'id': corpus.id,
                'filename': corpus.original_filename,
                'imported_at': corpus.imported_at.strftime('%d.%m.%Y %H:%M'),
                'author': corpus.global_metadata.get('author', 'Bilinmeyen'),
                'genre': corpus.global_metadata.get('genre', '-'),
                'token_count': corpus.document.get_word_count(),
                'sentence_count': corpus.sentence_count,
                'unique_lemmas': corpus.unique_lemmas,
                'format': corpus.get_source_format_display(),
                'format_code': corpus.source_format,
            })
        
        return JsonResponse({
            'corpora': corpora_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page': page_obj.number,
            'total_pages': paginator.num_pages
        })
    
    # Get unique values for filter dropdowns
    all_genres = set()
    all_authors = set()
    for corpus in CorpusMetadata.objects.only('global_metadata').all()[:500]:  # Limit for performance
        if corpus.global_metadata:
            if 'genre' in corpus.global_metadata:
                all_genres.add(corpus.global_metadata['genre'])
            if 'author' in corpus.global_metadata:
                all_authors.add(corpus.global_metadata['author'])
    
    context = {
        'corpora': page_obj,  # Pass page_obj instead of full queryset
        'page_obj': page_obj,  # Explicit naming for template clarity
        'all_genres': sorted(all_genres),
        'all_authors': sorted(all_authors),
        'format_choices': CorpusMetadata.FORMAT_CHOICES,
        'is_limited_public_view': is_limited_public_view,
        'active_tab': 'library'
    }
    return render(request, 'corpus/library.html', context)



@require_http_methods(["GET", "POST"])
def upload_view(request):
    """Handle corpus file upload and import (supports batch upload of VRT/CoNLL-U files)."""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        
        if not files:
            messages.error(request, '❌ Lütfen en az bir dosya seçin.')
            return redirect('corpus:upload')
        
        # Get corpus import options
        auto_detect = request.POST.get('auto_detect_format') == 'on'
        validate_format = request.POST.get('validate_format') == 'on'
        skip_duplicates = request.POST.get('skip_duplicates') == 'on'
        
        # Metadata
        metadata = {
            'author': request.POST.get('author', ''),
            'date': request.POST.get('date', ''),
            'source': request.POST.get('source', ''),
            'genre': request.POST.get('genre', ''),
            'language': request.POST.get('language', 'tr'),
            'publisher': request.POST.get('publisher', ''),
        }
        
        processed_count = 0
        failed_count = 0
        
        for uploaded_file in files:
            try:
                # Validate file extension
                import os
                from django.conf import settings
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
                    messages.warning(request, f'⚠️ {uploaded_file.name}: Desteklenmeyen format')
                    failed_count += 1
                    continue
                
                # Import corpus file
                try:
                    from django.core.management import call_command
                    import tempfile
                    
                    # Save uploaded file to temp location
                    # On Windows, we must close the file before opening it again in another handle
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                        for chunk in uploaded_file.chunks():
                            tmp_file.write(chunk)
                        tmp_path = tmp_file.name
                    
                    try:
                        # Call import_corpus command
                        # We pass the logged-in user so they own the document
                        call_command(
                            'import_corpus',
                            tmp_path,
                            title=metadata.get('source', uploaded_file.name),
                            author=metadata.get('author', ''),
                            genre=metadata.get('genre', 'other'),
                            user=request.user.username,
                            skip_duplicates=skip_duplicates,
                            format=ext[1:].replace('txt', 'vrt'), # Map txt to vrt or auto
                            validate=validate_format
                        )
                        processed_count += 1
                    finally:
                        # Clean up temp file
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)
                        
                except Exception as e:
                    messages.error(request, f'❌ {uploaded_file.name}: İmport hatası - {str(e)}')
                    failed_count += 1
                    continue
                    
            except Exception as e:
                messages.error(request, f'❌ {uploaded_file.name}: {str(e)}')
                failed_count += 1
        
        # Summary message
        if processed_count > 0:
            messages.success(
                request,
                f'✅ {processed_count} dosya başarıyla yüklendi ve işleme alındı!'
            )
        if failed_count > 0:
            messages.warning(request, f'⚠️ {failed_count} dosya yüklenemedi.')
        
        return redirect('corpus:library')
    else:
        form = DocumentUploadForm()
    
    context = {
        'form': form,
        'active_tab': 'upload'
    }
    return render(request, 'corpus/upload.html', context)


@ratelimit(key='user_or_ip', rate='100/d', method='GET')
def analysis_view(request, doc_id):
    """Display corpus analysis and KWIC search.
    
    Rate limit: 100 requests per day per user or IP address.
    """
    # Bypass rate limit for superusers
    if request.user.is_authenticated and request.user.is_superuser:
        request.limited = False
    
    document = get_object_or_404(Document, id=doc_id)
    
    if not document.processed:
        messages.warning(request, 'Bu belge henüz işlenmedi.')
        return redirect('corpus:library')
    
    # Initialize service
    service = CorpusService()
    
    # Get basic stats
    stats = service.get_statistics(document)
    
    # Handle search
    search_results = None
    if request.GET.get('query') or request.GET.get('search_type'):
        search_params = {
            'search_type': request.GET.get('search_type', 'word'),
            'keyword': request.GET.get('query', ''),
            'pos_tags': request.GET.getlist('pos_tags'),
            'context_size': int(request.GET.get('context_size', 5)),
            'regex': request.GET.get('regex') == 'true',
            'case_sensitive': request.GET.get('case_sensitive') == 'true',
            'lemma_filter': request.GET.get('lemma_filter', ''),
            'word_pattern': request.GET.get('word_pattern', ''),
            'min_confidence': float(request.GET.get('min_confidence', 0.0)),
            'max_confidence': float(request.GET.get('max_confidence', 1.0)),
        }
        
        search_results_list = service.search_in_document(document, search_params)
    
        # Pagination for Search Results
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
        paginator = Paginator(search_results_list, 50)  # 50 KWIC lines per page
        
        page_number = request.GET.get('page')
        try:
            search_results = paginator.get_page(page_number)
        except PageNotAnInteger:
            search_results = paginator.page(1)
        except EmptyPage:
            search_results = paginator.page(paginator.num_pages)
            
    # Get POS tags for filters
    pos_tags = []
    if hasattr(document, 'analysis') and document.analysis.data:
        pos_tags = list(set(
            item.get('pos', '') 
            for item in document.analysis.data 
            if isinstance(item, dict) and item.get('pos')
        ))
        pos_tags.sort()
    
    # Document Preview
    from .permissions import get_document_preview_limit, user_can_view_full_document
    preview_limit = get_document_preview_limit(request.user)
    preview_text = ""
    
    if hasattr(document, 'content') and document.content and document.content.cleaned_text:
        text = document.content.cleaned_text
        if preview_limit:
             # Simple word split for approximation
            words = text.split()
            if len(words) > preview_limit:
                preview_text = " ".join(words[:preview_limit]) + "..."
            else:
                preview_text = text
        else:
            # Full text for authorized users (maybe limit to a reasonable first chunk for display performance anyway)
            # But "view full document" rights imply they *can* see it. 
            # For this view, we might still want to truncate if it's huge, but let's assume we show a generous amount or full.
            preview_text = text[:10000] + "..." if len(text) > 10000 else text # Safety cap for rendering
    
    context = {
        'document': document,
        'stats': stats,
        'search_results': search_results, # Now this is a Page object
        'pos_tags': pos_tags,
        'active_tab': 'analysis',
        'preview_text': preview_text,
        'is_preview_limited': preview_limit is not None
    }
    return render(request, 'corpus/analysis.html', context)


def statistics_view(request):
    """Display corpus-wide linguistic statistics."""
    from .models import Token, Sentence, CorpusMetadata
    from django.db.models import Count
    from collections import Counter
    
    # Basic counts
    total_tokens = Token.objects.count()
    total_sentences = Sentence.objects.count()
    total_documents = CorpusMetadata.objects.count()
    
    # POS distribution (top 15) - using upos (Universal POS tags)
    pos_counts = Token.objects.values('upos').annotate(
        count=Count('id')
    ).order_by('-count')[:15]
    
    # Lemma diversity (unique lemmas)
    unique_lemmas = Token.objects.values('lemma').distinct().count()
    
    # Type-Token Ratio (TTR)
    unique_forms = Token.objects.values('form').distinct().count()
    ttr = round(unique_forms / total_tokens * 100, 2) if total_tokens > 0 else 0
    
    # Average sentence length
    avg_sentence_length = round(total_tokens / total_sentences, 2) if total_sentences > 0 else 0
    
    # Most frequent tokens (top 20)
    frequent_tokens = Token.objects.values('form', 'lemma').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    context = {
        'total_tokens': total_tokens,
        'total_sentences': total_sentences,
        'total_documents': total_documents,
        'unique_lemmas': unique_lemmas,
        'unique_forms': unique_forms,
        'ttr': ttr,
        'avg_sentence_length': avg_sentence_length,
        'pos_distribution': pos_counts,
        'frequent_tokens': frequent_tokens,
        'active_tab': 'statistics'
    }
    return render(request, 'corpus/corpus_statistics.html', context)


@login_required
@user_passes_test(is_academician)
@require_http_methods(["POST"])
def delete_document(request, doc_id):
    """Delete a document."""
    document = get_object_or_404(Document, id=doc_id)
    filename = document.filename
    document.delete()
    
    messages.success(request, f'✅ {filename} silindi.')
    return redirect('corpus:library')


@login_required
@ratelimit(key='user', rate='50/d', method='POST')
def download_search_results(request, doc_id):
    """Download KWIC search results as CSV.
    
    Rate limit: 50 downloads per day per user.
    """
    # Bypass rate limit for superusers
    if request.user.is_superuser:
        request.limited = False
    
    from .permissions import user_can_export
    if not user_can_export(request.user):
        messages.error(request, 'Bu işlem için yetkiniz yok. (Öğrenci veya üstü üyelik gerektirir)')
        return redirect('corpus:analysis', doc_id=doc_id)

    document = get_object_or_404(Document, id=doc_id)
    
    if not document.processed or not hasattr(document, 'analysis'):
        messages.error(request, 'Bu belge henüz analiz edilmedi.')
        return redirect('corpus:library')
    
    # Get search params
    search_query = request.GET.get('query', '')
    search_type = request.GET.get('search_type', 'word')
    
    if not search_query:
        messages.error(request, 'Arama sorgusu gerekli.')
        return redirect('corpus:analysis', doc_id=doc_id)
    
    # Perform search using CorpusService
    service = CorpusService()
    search_params = {
        'search_type': search_type,
        'keyword': search_query,
        'context_size': int(request.GET.get('context_size', 5)),
        'case_sensitive': request.GET.get('case_sensitive') == 'true',
        'regex': request.GET.get('regex') == 'true'
    }
    search_results = service.search_in_document(document, search_params)
    
    # Create CSV response
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="kwic_results_{document.filename}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Sol Bağlam', 'Anahtar Kelime', 'Sağ Bağlam', 'POS', 'Lemma'])
    
    for result in search_results:
        writer.writerow([
            result.get('left_context', ''),
            result.get('keyword', ''),
            result.get('right_context', ''),
            result.get('pos', '-'),
            result.get('lemma', '-')
        ])
    
    return response


@login_required
def export_document(request, doc_id):
    """Export document in specified format."""
    from .permissions import user_can_export
    if not user_can_export(request.user):
        messages.error(request, 'Bu işlem için yetkiniz yok.')
        # Redirect based on user role/status
        return redirect('corpus:analysis', doc_id=doc_id)

    document = get_object_or_404(Document, id=doc_id)
    
    if not document.processed:
        messages.error(request, 'Bu belge henüz işlenmedi.')
        return redirect('corpus:library')
    
    export_format = request.GET.get('format', 'json')
    service = CorpusService()
    
    content = service.export_document(
        document, 
        export_format=export_format,
        include_structure=(export_format == 'vrt')
    )
    
    if content is None:
        messages.error(request, 'Export başarısız.')
        return redirect('corpus:analysis', doc_id=doc_id)
    
    # Set content type
    content_types = {
        'json': 'application/json',
        'csv': 'text/csv',
        'conllu': 'text/plain',
        'vrt': 'text/xml'
    }
    
    response = HttpResponse(content, content_type=content_types.get(export_format, 'text/plain'))
    response['Content-Disposition'] = f'attachment; filename="{document.filename}.{export_format}"'
    
    return response


def task_status_view(request, task_id):
    """Get task status (for AJAX polling)."""
    try:
        task = ProcessingTask.objects.get(task_id=task_id)
        return JsonResponse({
            'status': task.status,
            'progress': task.progress,
            'error': task.error_message,
            'document_id': task.document.id
        })
    except ProcessingTask.DoesNotExist:
        return JsonResponse({'error': 'Task not found'}, status=404)


# Authentication Views
def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('corpus:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Get user role for personalized message
            role = "Süper Kullanıcı" if user.is_superuser else (
                user.groups.first().name if user.groups.exists() else "Kullanıcı"
            )
            
            welcome_name = user.get_full_name() or user.username
            messages.success(
                request, 
                f'🎉 Hoş geldiniz, {welcome_name}! ({role})'
            )
            
            next_url = request.GET.get('next', 'corpus:home')
            return redirect(next_url)
        else:
            messages.error(request, '❌ Kullanıcı adı veya şifre hatalı. Lütfen tekrar deneyin.')
    
    return render(request, 'corpus/login.html')


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('corpus:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        if not username or not email or not password1:
            messages.error(request, '⚠️ Lütfen tüm zorunlu alanları doldurun.')
            return render(request, 'corpus/register.html')
        
        if password1 != password2:
            messages.error(request, '🔒 Şifreler eşleşmiyor. Lütfen aynı şifreyi girin.')
            return render(request, 'corpus/register.html')
        
        if len(password1) < 8:
            messages.error(request, '🔑 Şifre en az 8 karakter olmalıdır.')
            return render(request, 'corpus/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, '👤 Bu kullanıcı adı zaten kullanılıyor. Lütfen başka bir kullanıcı adı seçin.')
            return render(request, 'corpus/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, '✉️ Bu e-posta adresi zaten kullanılıyor.')
            return render(request, 'corpus/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name
        )
        
        messages.success(
            request, 
            f'✅ Hesabınız başarıyla oluşturuldu! Hoş geldiniz {first_name or username}, şimdi giriş yapabilirsiniz.'
        )
        return redirect('corpus:login')
    
    return render(request, 'corpus/register.html')


def logout_view(request):
    """User logout view."""
    # Safely get user display name — AnonymousUser may not have get_full_name
    if request.user.is_authenticated:
        try:
            username = request.user.get_full_name() or request.user.username
        except Exception:
            username = getattr(request.user, 'username', None)
    else:
        username = None

    logout(request)

    # Use a generic message if we don't have a username
    if username:
        messages.success(request, f'👋 Görüşmek üzere, {username}! Başarıyla çıkış yaptınız.')
    else:
        messages.success(request, '👋 Başarıyla çıkış yaptınız.')

    # Show a centered logout confirmation page, then redirect to home shortly.
    return render(request, 'corpus/logout.html', {
        'username': username
    })


@login_required
@login_required
def profile_view(request):
    """User profile view with role info and quota tracking."""
    # Get or create UserProfile
    from .models import UserProfile, QueryLog, ExportLog
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Reset quotas if needed
    profile.reset_query_count_if_needed()
    profile.reset_export_quota_if_needed()
    
    # Calculate quota percentages
    query_limit = profile.get_query_limit()
    query_percentage = (profile.queries_today / query_limit * 100) if query_limit else 0
    
    export_percentage = (profile.export_used_mb / profile.export_quota_mb * 100) if profile.export_quota_mb > 0 else 0
    
    # Get recent search history (old model)
    recent_searches = request.user.search_history.order_by('-created_at')[:10]
    
    # Get recent query logs (NEW - detailed activity)
    recent_query_logs = QueryLog.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Get recent export logs
    recent_export_logs = ExportLog.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'active_tab': 'profile',
        'profile': profile,
        'query_limit': query_limit,
        'query_percentage': query_percentage,
        'export_percentage': export_percentage,
        'recent_searches': recent_searches,
        'recent_query_logs': recent_query_logs,
        'recent_export_logs': recent_export_logs,
    }
    
    return render(request, 'corpus/profile.html', context)



@login_required
@ratelimit(key='user', rate='200/h', method='GET')
def global_search_view(request):
    """Global search endpoint for documents and collections (AJAX).
    
    Rate limit: 200 requests per hour per user.
    """
    # Bypass rate limit for superusers
    if request.user.is_superuser:
        request.limited = False
    
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'basic')  # basic, fuzzy, regex, advanced
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    # Track search history for authenticated users
    if request.user.is_authenticated:
        from .models import SearchHistory
        SearchHistory.objects.create(
            user=request.user,
            query=query,
            search_type=search_type
        )
    
    # Search based on type
    if search_type == 'regex':
        # Regex search
        try:
            import re
            from django.db.models import Q
            pattern = re.compile(query, re.IGNORECASE)

            # Limit to processed documents that have extracted content for performance
            documents_qs = Document.objects.filter(processed=True).select_related('content').order_by('-upload_date')[:200]

            matching_docs = []
            for doc in documents_qs:
                # Check title
                if doc.title and pattern.search(doc.title):
                    matching_docs.append(doc)
                    continue

                # Check author
                if doc.author and pattern.search(doc.author):
                    matching_docs.append(doc)
                    continue

                # Check content (cleaned_text)
                if hasattr(doc, 'content') and doc.content and doc.content.cleaned_text:
                    try:
                        if pattern.search(doc.content.cleaned_text):
                            matching_docs.append(doc)
                            continue
                    except Exception:
                        # If content is extremely large or pattern fails, skip safely
                        pass

                # Check metadata values (stringified)
                if doc.metadata:
                    meta_text = ' '.join([str(v) for v in doc.metadata.values() if v])
                    if meta_text and pattern.search(meta_text):
                        matching_docs.append(doc)
                        continue

            # Return top matches
            documents = matching_docs[:30]
        except re.error:
            return JsonResponse({'error': 'Invalid regex pattern'}, status=400)
    
    elif search_type == 'fuzzy':
        # Fuzzy search using Django's trigram similarity (PostgreSQL)
        try:
            from django.contrib.postgres.search import TrigramSimilarity
            documents = Document.objects.annotate(
                similarity=TrigramSimilarity('title', query) + TrigramSimilarity('author', query)
            ).filter(similarity__gt=0.1).order_by('-similarity')[:10]
        except:
            # Fallback to basic search if PostgreSQL not available
            from django.db.models import Q
            documents = Document.objects.filter(
                Q(title__icontains=query) |
                Q(author__icontains=query) |
                Q(content__cleaned_text__icontains=query) |
                Q(metadata__author__icontains=query) |
                Q(metadata__source__icontains=query)
            )
            documents = documents.distinct()[:10]
    
    else:
        # Basic search across title, author, content and common metadata
        from django.db.models import Q
        documents = Document.objects.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(content__cleaned_text__icontains=query) |
            Q(metadata__author__icontains=query) |
            Q(metadata__source__icontains=query)
        ).distinct()[:10]
    
    for doc in documents:
        metadata_parts = []
        if doc.author:
            metadata_parts.append(doc.author)
        if doc.upload_date:
            metadata_parts.append(doc.upload_date.strftime('%d.%m.%Y'))
        
        results.append({
            'type': 'document',
            'title': doc.title,
            'url': f'/corpus/library/?doc={doc.id}',
            'metadata': ' • '.join(metadata_parts),
            'badge': f'{doc.get_word_count()} kelime' if doc.processed else 'İşleniyor',
            'badge_icon': 'article' if doc.processed else 'hourglass_empty'
        })
    
    # Search in collections
    collections = Collection.objects.filter(name__icontains=query)[:5]
    
    for coll in collections:
        doc_count = coll.get_document_count()
        results.append({
            'type': 'collection',
            'title': coll.name,
            'url': f'/corpus/collections/{coll.id}/',
            'metadata': coll.description[:100] if coll.description else 'Açıklama yok',
            'badge': f'{doc_count} belge',
            'badge_icon': 'folder'
        })
    
    # Update result count in search history
    if request.user.is_authenticated:
        try:
            last_search = SearchHistory.objects.filter(user=request.user).first()
            if last_search:
                last_search.result_count = len(results)
                last_search.save()
        except:
            pass
    
    return JsonResponse({'results': results})


def search_suggestions_view(request):
    """Provide simple autocomplete suggestions for search input."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)

    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'suggestions': []})

    suggestions = []

    # Recent searches for authenticated users
    if request.user.is_authenticated:
        from .models import SearchHistory
        recent = SearchHistory.objects.filter(user=request.user).order_by('-created_at')[:5]
        for r in recent:
            if q.lower() in r.query.lower():
                suggestions.append({'type': 'recent', 'value': r.query})

    # Titles and authors matching prefix
    from django.db.models import Q
    docs = Document.objects.filter(Q(filename__icontains=q) | Q(author__icontains=q)).distinct()[:8]
    for d in docs:
        if q.lower() in (d.filename or '').lower():
            suggestions.append({'type': 'title', 'value': d.filename})
        elif d.author and q.lower() in d.author.lower():
            suggestions.append({'type': 'author', 'value': d.author})

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in suggestions:
        key = f"{s['type']}:{s['value']}"
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return JsonResponse({'suggestions': unique})


# ============================================================================
# Tag Management Views
# ============================================================================

@login_required
@require_http_methods(["POST"])
def add_tag_to_document(request, doc_id):
    """Add a tag to a document (create if doesn't exist)."""
    from .models import Tag
    import json
    
    try:
        data = json.loads(request.body)
        tag_name = data.get('tag_name', '').strip()
        tag_color = data.get('tag_color', 'blue')
        
        if not tag_name:
            return JsonResponse({'success': False, 'error': 'Tag adı gerekli'}, status=400)
        
        document = Document.objects.get(id=doc_id)
        
        # Create or get tag
        from django.utils.text import slugify
        tag, created = Tag.objects.get_or_create(
            name=tag_name,
            defaults={'slug': slugify(tag_name), 'color': tag_color}
        )
        
        # Add tag to document
        document.tags.add(tag)
        
        return JsonResponse({
            'success': True,
            'tag': {
                'name': tag.name,
                'slug': tag.slug,
                'color': tag.color
            },
            'created': created
        })
        
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Belge bulunamadı'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def remove_tag_from_document(request, doc_id, tag_slug):
    """Remove a tag from a document."""
    from .models import Tag
    
    try:
        document = Document.objects.get(id=doc_id)
        tag = Tag.objects.get(slug=tag_slug)
        
        document.tags.remove(tag)
        
        return JsonResponse({'success': True})
        
    except Document.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Belge bulunamadı'}, status=404)
    except Tag.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tag bulunamadı'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def bulk_add_tags(request):
    """Add tags to multiple documents."""
    from .models import Tag
    import json
    
    try:
        data = json.loads(request.body)
        doc_ids = data.get('document_ids', [])
        tag_names = data.get('tag_names', [])
        
        if not doc_ids or not tag_names:
            return JsonResponse({
                'success': False, 
                'error': 'Belge ID\'leri ve tag isimleri gerekli'
            }, status=400)
        
        documents = Document.objects.filter(id__in=doc_ids)
        
        from django.utils.text import slugify
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(
                name=tag_name.strip(),
                defaults={'slug': slugify(tag_name.strip())}
            )
            
            for doc in documents:
                doc.tags.add(tag)
        
        return JsonResponse({
            'success': True,
            'count': len(doc_ids),
            'message': f'{len(doc_ids)} belgeye {len(tag_names)} tag eklendi'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
