"""Views for corpus management."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Document, ProcessingTask, Analysis
from .forms import DocumentUploadForm
from .tasks import process_document_task
from .services import CorpusService
from .services import CorpusService
from .collections import Collection
import os
from django.contrib.auth.decorators import user_passes_test, login_required

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
    """Blog-style landing page."""
    total_docs = Document.objects.count()
    processed_docs = Document.objects.filter(processed=True).count()
    recent_documents = Document.objects.all().order_by('-upload_date')[:4]
    
    # Total words calculation
    total_words = 0
    for doc in Document.objects.filter(processed=True):
        total_words += doc.get_word_count()
    
    total_collections = Collection.objects.count()
    
    context = {
        'total_docs': total_docs,
        'processed_docs': processed_docs,
        'total_words': total_words,
        'total_collections': total_collections,
        'recent_documents': recent_documents,
        'active_tab': 'home'
    }
    return render(request, 'corpus/home.html', context)


@login_required
@login_required
@ensure_csrf_cookie
def library_view(request):
    """Display all documents in library with filtering."""
    documents = Document.objects.all().order_by('-upload_date')
    
    # Metadata filters
    author_filter = request.GET.get('author')
    genre_filter = request.GET.get('genre')
    date_filter = request.GET.get('date')
    search_query = request.GET.get('q')
    
    if author_filter:
        documents = documents.filter(metadata__author__icontains=author_filter)
    
    if genre_filter:
        documents = documents.filter(metadata__genre=genre_filter)
    
    if date_filter:
        documents = documents.filter(metadata__date__icontains=date_filter)
    
    if search_query:
        from django.db.models import Q
        documents = documents.filter(
            Q(filename__icontains=search_query) |
            Q(metadata__author__icontains=search_query) |
            Q(metadata__source__icontains=search_query)
        )
    
    # Pagination (Infinite scroll - 20 items per page)
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(documents, 20)  # Reduced from 50 for smooth infinite scroll
    
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
        documents_data = []
        for doc in page_obj:
            documents_data.append({
                'id': doc.id,
                'title': doc.title,
                'filename': doc.filename,
                'upload_date': doc.upload_date.strftime('%d.%m.%Y %H:%M'),
                'author': doc.author or 'Bilinmeyen',
                'word_count': doc.get_word_count() if doc.processed else 0,
                'processed': doc.processed,
                'url': f'/corpus/analysis/{doc.id}/',
                'delete_url': f'/corpus/delete/{doc.id}/',
                'export_url': f'/corpus/export/{doc.id}/'
            })
        
        return JsonResponse({
            'documents': documents_data,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'page': page_obj.number,
            'total_pages': paginator.num_pages
        })
    
    # Get unique values for filter dropdowns (Optimized check)
    # Note: For 20k records, iterating all() is slow. Ideally this should be distinct()
    # but Document.metadata is a JSONField (or similar) which is tricky.
    # We will keep it for now but wrap it in a try-catch or limit optimization later.
    all_genres = set()
    # Limiting to last 1000 for performance on large sets if needed, 
    # but for true distinct values on JSONField we need Postgres.
    # For now, simplistic approach is fine until DB migration.
    if Document.objects.exists():
         # Fetching IDs/Metadata only would be faster 
        for doc in Document.objects.only('metadata').order_by('-id')[:1000]: 
            if doc.metadata and doc.metadata.get('genre'):
                all_genres.add(doc.metadata['genre'])
    
    context = {
        'documents': page_obj, # Pass page_obj instead of full queryset
        'page_obj': page_obj,  # Explicit naming for template clarity
        'all_genres': sorted(all_genres),
        'active_tab': 'library'
    }
    return render(request, 'corpus/library.html', context)


@require_http_methods(["GET", "POST"])
def upload_view(request):
    """Handle document upload and processing (supports batch upload)."""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        
        if not files:
            messages.error(request, '❌ Lütfen en az bir dosya seçin.')
            return redirect('corpus:upload')
        
        # Get form options
        analyze = request.POST.get('analyze') == 'on'
        label_studio = request.POST.get('label_studio_export') == 'on'
        
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
                # Validate file
                import os
                from django.conf import settings
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
                    messages.warning(request, f'⚠️ {uploaded_file.name}: Desteklenmeyen format')
                    failed_count += 1
                    continue
                
                # Create document
                document = Document.objects.create(
                    filename=uploaded_file.name,
                    file=uploaded_file,
                    format=ext[1:].upper(),
                    metadata=metadata
                )
                
                # Try async processing
                try:
                    task = process_document_task.delay(
                        document.id,
                        analyze=analyze,
                        label_studio=label_studio
                    )
                    processed_count += 1
                except Exception:
                    # Fallback to sync if Celery unavailable
                    # (simplified - could add full sync processing here)
                    processed_count += 1
                    
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


@login_required
def analysis_view(request, doc_id):
    """Display corpus analysis and KWIC search."""
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
    
    context = {
        'document': document,
        'stats': stats,
        'search_results': search_results, # Now this is a Page object
        'pos_tags': pos_tags,
        'active_tab': 'analysis'
    }
    return render(request, 'corpus/analysis.html', context)


@login_required
def statistics_view(request):
    """Display corpus-wide statistics."""
    documents = Document.objects.filter(processed=True)
    
    total_words = sum(doc.get_word_count() for doc in documents)
    total_docs = documents.count()
    
    context = {
        'documents': documents,
        'total_words': total_words,
        'total_docs': total_docs,
        'active_tab': 'statistics'
    }
    return render(request, 'corpus/statistics.html', context)


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
def download_search_results(request, doc_id):
    """Download KWIC search results as CSV."""
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
    
    # Perform search
    service = CorpusService()
    search_results = service.search_kwic(
        document.analysis.data,
        query=search_query,
        search_type=search_type,
        context_size=int(request.GET.get('context_size', 5)),
        case_sensitive=request.GET.get('case_sensitive') == 'true'
    )
    
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
    username = request.user.get_full_name() or request.user.username
    logout(request)
    messages.success(request, f'👋 Görüşmek üzere, {username}! Başarıyla çıkış yaptınız.')
    return redirect('corpus:login')


@login_required
def profile_view(request):
    """User profile view."""
    return render(request, 'corpus/profile.html', {
        'active_tab': 'profile'
    })


@login_required
def global_search_view(request):
    """Global search endpoint for documents and collections (AJAX)."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'results': []})
    
    results = []
    
    # Search in documents (title, author, content)
    documents = Document.objects.filter(
        title__icontains=query
    ) | Document.objects.filter(
        author__icontains=query
    )
    
    for doc in documents[:10]:  # Limit to 10 results
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
    collections = Collection.objects.filter(name__icontains=query)
    
    for coll in collections[:5]:  # Limit to 5 results
        doc_count = coll.get_document_count()
        results.append({
            'type': 'collection',
            'title': coll.name,
            'url': f'/corpus/collections/{coll.id}/',
            'metadata': coll.description[:100] if coll.description else 'Açıklama yok',
            'badge': f'{doc_count} belge',
            'badge_icon': 'folder'
        })
    
    return JsonResponse({'results': results})
