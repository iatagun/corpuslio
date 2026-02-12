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
# Upload form removed; uploads are handled via admin/import_corpus
from .services import CorpusService
from .services import CorpusService
from .collections import Collection
from .utils import check_password_strength, send_verification_email, log_login_attempt
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
    
    total_collections = 0
    if request.user.is_authenticated:
        total_collections = Collection.objects.filter(owner=request.user).count()
    
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



# Note: Upload functionality removed from public UI; imports are handled via admin/import_corpus.


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
    
    # Document Preview: universally limit preview to first 300 characters for all users
    preview_text = ""
    preview_char_limit = 300

    if hasattr(document, 'content') and document.content and document.content.cleaned_text:
        text = document.content.cleaned_text
        preview_text = text[:preview_char_limit]
        if len(text) > preview_char_limit:
            preview_text = preview_text.rstrip() + "..."
        is_preview_limited = True
    
    context = {
        'document': document,
        'stats': stats,
        'search_results': search_results, # Now this is a Page object
        'pos_tags': pos_tags,
        'active_tab': 'analysis',
        'preview_text': preview_text,
        'is_preview_limited': is_preview_limited
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
@ratelimit(key='ip', rate='20/m', method='POST', block=False)
@ratelimit(key='post:username', rate='10/m', method='POST', block=False)
def login_view(request):
    """User login view with email verification and security features (Task 11.9)."""
    if request.user.is_authenticated:
        return redirect('corpus:home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        # If user entered an email instead of username, resolve it to username
        resolved_username = username
        if '@' in username:
            try:
                u = User.objects.get(email__iexact=username)
                resolved_username = u.username
            except User.DoesNotExist:
                # keep resolved_username as entered (will fail authentication)
                resolved_username = username

        # Try to authenticate
        user = authenticate(request, username=resolved_username, password=password)
        
        if user is not None:
            # Check if email is verified (Task 11.9)
            if not user.profile.email_verified:
                # Log failed login (email not verified)
                log_login_attempt(
                    request=request,
                    user=user,
                    username_attempted=username,
                    success=False,
                    failure_reason='email_not_verified'
                )
                
                messages.error(
                    request,
                    '✉️ Email adresiniz henüz doğrulanmamış. '
                    'Lütfen email adresinize gönderilen doğrulama linkine tıklayın.'
                )
                # Store email in session for resend option
                request.session['pending_verification_email'] = user.email
                
                # Show resend link in message
                messages.info(
                    request,
                    'Doğrulama emaili almadıysanız, '
                    '<a href="/tr/auth/verification-sent/" style="color: #667eea; text-decoration: underline;">buraya tıklayarak</a> '
                    'yeni bir doğrulama emaili isteyebilirsiniz.'
                )
                return render(request, 'corpus/login.html')
            
            # Check if account is locked (Task 11.9)
            if user.profile.is_account_locked():
                from datetime import datetime
                lock_until = user.profile.account_locked_until
                remaining_minutes = int((lock_until - datetime.now(lock_until.tzinfo)).total_seconds() / 60)
                
                # Log failed login (account locked)
                log_login_attempt(
                    request=request,
                    user=user,
                    username_attempted=username,
                    success=False,
                    failure_reason='account_locked'
                )
                
                messages.error(
                    request,
                    f'🔒 Hesabınız çok fazla başarısız giriş denemesi nedeniyle kilitlendi. '
                    f'Lütfen {remaining_minutes} dakika sonra tekrar deneyin.'
                )
                return render(request, 'corpus/login.html')
            
            # Successful login - reset failed attempts
            user.profile.reset_failed_login_attempts()
            
            login(request, user)
            
            # Log successful login attempt (Task 11.15)
            log_login_attempt(
                request=request,
                user=user,
                username_attempted=username,
                success=True,
                session_key=request.session.session_key
            )
            
            # Get user role for personalized message
            role = "Süper Kullanıcı" if user.is_superuser else (
                user.profile.get_role_display() if hasattr(user, 'profile') else "Kullanıcı"
            )
            
            welcome_name = user.get_full_name() or user.username
            messages.success(
                request, 
                f'🎉 Hoş geldiniz, {welcome_name}! ({role})'
            )
            
            next_url = request.GET.get('next', 'corpus:home')
            return redirect(next_url)
        else:
            # Failed login - record attempt (Task 11.9)
            # Try to find user by username to track failed attempts
            try:
                # Try resolved_username first (handles email input)
                failed_user = User.objects.get(username=resolved_username)
                failed_user.profile.record_failed_login()
                
                # Log failed login attempt (invalid credentials)
                log_login_attempt(
                    request=request,
                    user=failed_user,
                    username_attempted=username,
                    success=False,
                    failure_reason='invalid_credentials'
                )
                
                # Check if account just got locked
                if failed_user.profile.is_account_locked():
                    messages.error(
                        request,
                        '🔒 Çok fazla başarısız giriş denemesi yaptınız. '
                        'Hesabınız güvenlik nedeniyle 30 dakika süreyle kilitlendi.'
                    )
                else:
                    remaining_attempts = 5 - failed_user.profile.failed_login_attempts
                    if remaining_attempts <= 2:
                        messages.error(
                            request,
                            f'❌ Kullanıcı adı veya şifre hatalı. '
                            f'Kalan deneme hakkınız: {remaining_attempts}'
                        )
                    else:
                        messages.error(request, '❌ Kullanıcı adı veya şifre hatalı. Lütfen tekrar deneyin.')
            except User.DoesNotExist:
                # User not found - don't reveal this info
                # Log failed login attempt (user not found)
                log_login_attempt(
                    request=request,
                    user=None,
                    username_attempted=username,
                    success=False,
                    failure_reason='user_not_found'
                )
                messages.error(request, '❌ Kullanıcı adı veya şifre hatalı. Lütfen tekrar deneyin.')
    
    return render(request, 'corpus/login.html')


@ratelimit(key='ip', rate='5/h', method='POST', block=False)
@ratelimit(key='post:email', rate='3/d', method='POST', block=False)
def register_view(request):
    """User registration view with email verification (Task 11.5)."""
    if request.user.is_authenticated:
        return redirect('corpus:home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Basic validation
        if not username or not email or not password1:
            messages.error(request, '⚠️ Lütfen tüm zorunlu alanları doldurun.')
            return render(request, 'corpus/register.html')
        
        # Email format validation
        if '@' not in email or '.' not in email.split('@')[-1]:
            messages.error(request, '✉️ Geçerli bir email adresi girin.')
            return render(request, 'corpus/register.html')
        
        # Username validation (alphanumeric + underscore)
        if not username.replace('_', '').isalnum():
            messages.error(request, '👤 Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir.')
            return render(request, 'corpus/register.html')
        
        # Password confirmation
        if password1 != password2:
            messages.error(request, '🔒 Şifreler eşleşmiyor. Lütfen aynı şifreyi iki kez girin.')
            return render(request, 'corpus/register.html')
        
        # Password strength validation (Task 11.5)
        is_valid, errors = check_password_strength(password1)
        if not is_valid:
            for error in errors:
                messages.error(request, f'🔑 {error}')
            return render(request, 'corpus/register.html')
        
        # Check username uniqueness
        if User.objects.filter(username=username).exists():
            messages.error(request, '👤 Bu kullanıcı adı zaten kullanılıyor. Lütfen başka bir kullanıcı adı seçin.')
            return render(request, 'corpus/register.html')
        
        # Check email uniqueness
        if User.objects.filter(email=email).exists():
            messages.error(request, '✉️ Bu email adresi zaten kayıtlı. Giriş yapmayı deneyin veya şifrenizi sıfırlayın.')
            return render(request, 'corpus/register.html')
        
        # Create user (inactive until email verification)
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
                is_active=False  # Will be activated after email verification
            )
            
            # Send verification email
            success, error_msg = send_verification_email(user, request)
            
            if success:
                messages.success(
                    request,
                    f'✅ Hesabınız oluşturuldu! Email adresinize ({email}) bir doğrulama linki gönderdik. '
                    f'Hesabınızı aktif etmek için lütfen emailinizi kontrol edin.'
                )
                # Store email in session for resend functionality
                request.session['pending_verification_email'] = email
                return redirect('corpus:verification_sent')
            else:
                # Email sending failed - delete user and show error
                user.delete()
                messages.error(
                    request,
                    f'❌ Doğrulama emaili gönderilemedi. Lütfen daha sonra tekrar deneyin. '
                    f'Hata: {error_msg}'
                )
                return render(request, 'corpus/register.html')
                
        except Exception as e:
            messages.error(request, f'❌ Hesap oluşturulurken bir hata oluştu: {str(e)}')
            return render(request, 'corpus/register.html')
    
    return render(request, 'corpus/register.html')


def ratelimit_handler(request, exception=None):
    """
    Custom handler for rate limit exceptions (Task 11.10).
    Shows user-friendly error message when rate limits are exceeded.
    """
    # Determine which action was rate limited based on request path
    path = request.path
    
    if 'login' in path:
        error_message = (
            '🚫 Çok fazla giriş denemesi yaptınız. '
            'Lütfen birkaç dakika bekleyip tekrar deneyin. '
            'Güvenliğiniz için giriş denemeleri sınırlıdır.'
        )
    elif 'register' in path:
        error_message = (
            '🚫 Çok fazla kayıt denemesi yaptınız. '
            'Lütfen bir süre bekleyip tekrar deneyin. '
            'Spam önleme sistemimiz kayıt sayısını sınırlar.'
        )
    elif 'resend-verification' in path:
        error_message = (
            '✉️ Çok fazla doğrulama emaili isteği gönderidiniz. '
            'Lütfen spam klasörünüzü kontrol edin ve bir süre sonra tekrar deneyin.'
        )
    else:
        error_message = (
            '🚫 İşlem limiti aşıldı. '
            'Lütfen birkaç dakika bekleyip tekrar deneyin.'
        )
    
    from django.shortcuts import render
    from django.contrib import messages
    
    messages.error(request, error_message)
    
    # Render appropriate template based on request path
    if 'login' in path:
        return render(request, 'corpus/login.html', status=429)
    elif 'register' in path:
        return render(request, 'corpus/register.html', status=429)
    elif 'verification' in path:
        return render(request, 'corpus/email_verification_sent.html', status=429)
    else:
        # Generic error page
        return render(request, 'corpus/error.html', {
            'error_title': 'İşlem Limiti Aşıldı',
            'error_message': error_message
        }, status=429)


def email_verification_sent_view(request):
    """Display 'check your email' message after registration (Task 11.6)."""
    # Get email from session (set during registration)
    email = request.session.get('pending_verification_email')
    
    if not email:
        # No pending verification - redirect to register
        messages.info(request, 'Lütfen önce kayıt olun.')
        return redirect('corpus:register')
    
    context = {
        'email': email,
    }
    return render(request, 'corpus/email_verification_sent.html', context)


def email_verify_view(request, token):
    """Verify email address using token and activate user account (Task 11.6)."""
    from .utils import verify_email_token
    
    # Validate token and activate user
    success, message, user = verify_email_token(token)
    
    if success:
        messages.success(request, f'✅ {message}')
        # Clear pending verification from session
        if 'pending_verification_email' in request.session:
            del request.session['pending_verification_email']
        
        context = {
            'success': True,
            'user': user,
        }
        return render(request, 'corpus/email_verified.html', context)
    else:
        messages.error(request, f'❌ {message}')
        context = {
            'success': False,
            'message': message,
            'user': user,  # May be None if token invalid
        }
        return render(request, 'corpus/email_verified.html', context)


@ratelimit(key='user_or_ip', rate='3/h', method='POST')
def resend_verification_view(request):
    """Resend verification email with rate limiting (Task 11.6)."""
    if request.method != 'POST':
        return redirect('corpus:verification_sent')
    
    # Check rate limit
    was_limited = getattr(request, 'limited', False)
    if was_limited:
        messages.error(
            request,
            '⏱️ Çok fazla email gönderme denemesi yaptınız. '
            'Lütfen 1 saat sonra tekrar deneyin.'
        )
        return redirect('corpus:verification_sent')
    
    email = request.session.get('pending_verification_email')
    
    if not email:
        messages.error(request, 'Email adresi bulunamadı. Lütfen tekrar kayıt olun.')
        return redirect('corpus:register')
    
    try:
        # Find user by email
        user = User.objects.get(email=email, is_active=False)
        
        # Check if already verified
        if user.profile.email_verified:
            messages.info(request, 'Email adresiniz zaten doğrulanmış. Giriş yapabilirsiniz.')
            return redirect('corpus:login')
        
        # Resend verification email
        success, error_msg = send_verification_email(user, request)
        
        if success:
            messages.success(
                request,
                f'✅ Doğrulama emaili tekrar gönderildi. Lütfen {email} adresini kontrol edin.'
            )
        else:
            messages.error(
                request,
                f'❌ Email gönderilemedi. Lütfen daha sonra tekrar deneyin. Hata: {error_msg}'
            )
    
    except User.DoesNotExist:
        messages.error(request, 'Bu email ile kayıtlı aktif olmayan kullanıcı bulunamadı.')
    except Exception as e:
        messages.error(request, f'❌ Bir hata oluştu: {str(e)}')
    
    return redirect('corpus:verification_sent')


@ratelimit(key='ip', rate='5/h', method='POST')
def password_reset_request_view(request):
    """Request password reset - send email with reset link (Task 11.12)."""
    if request.user.is_authenticated:
        # Already logged in users should use change password
        messages.info(request, 'Zaten giriş yapmışsınız. Şifrenizi profil ayarlarından değiştirebilirsiniz.')
        return redirect('corpus:profile')
    
    if request.method == 'POST':
        # Check rate limit
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(
                request,
                '⏱️ Çok fazla şifre sıfırlama denemesi yaptınız. '
                'Lütfen 1 saat sonra tekrar deneyin.'
            )
            return render(request, 'corpus/password_reset_request.html')
        
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Lütfen email adresinizi girin.')
            return render(request, 'corpus/password_reset_request.html')
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
            
            # Send password reset email
            from .utils import send_password_reset_email
            success, error_msg = send_password_reset_email(user, request)
            
            if success:
                # Always show success message for security (don't reveal if email exists)
                messages.success(
                    request,
                    f'✅ Eğer {email} adresi sistemimizde kayıtlıysa, şifre sıfırlama linki gönderildi. '
                    'Lütfen email kutunuzu kontrol edin.'
                )
                return redirect('corpus:password_reset_sent')
            else:
                messages.error(
                    request,
                    f'❌ Email gönderilemedi. Lütfen daha sonra tekrar deneyin.'
                )
        
        except User.DoesNotExist:
            # Don't reveal that user doesn't exist (security best practice)
            messages.success(
                request,
                f'✅ Eğer {email} adresi sistemimizde kayıtlıysa, şifre sıfırlama linki gönderildi. '
                'Lütfen email kutunuzu kontrol edin.'
            )
            return redirect('corpus:password_reset_sent')
        
        except Exception as e:
            messages.error(request, f'❌ Bir hata oluştu: {str(e)}')
            return render(request, 'corpus/password_reset_request.html')
    
    return render(request, 'corpus/password_reset_request.html')


def password_reset_sent_view(request):
    """Show confirmation that reset email was sent (Task 11.12)."""
    return render(request, 'corpus/password_reset_sent.html')


def password_reset_confirm_view(request, token):
    """Confirm password reset with token and set new password (Task 11.12)."""
    from .utils import verify_password_reset_token, check_password_strength
    
    # Verify token first
    success, message, user = verify_password_reset_token(token)
    
    if not success or not user:
        messages.error(request, message)
        context = {
            'success': False,
            'message': message,
            'token': None,
        }
        return render(request, 'corpus/password_reset_confirm.html', context)
    
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        # Check if passwords match
        if password1 != password2:
            messages.error(request, '❌ Şifreler eşleşmiyor. Lütfen aynı şifreyi iki kez girin.')
            context = {
                'success': True,
                'token': token,
                'user': user,
            }
            return render(request, 'corpus/password_reset_confirm.html', context)
        
        # Check password strength
        is_valid, errors = check_password_strength(password1)
        if not is_valid:
            for error in errors:
                messages.error(request, f'🔑 {error}')
            context = {
                'success': True,
                'token': token,
                'user': user,
            }
            return render(request, 'corpus/password_reset_confirm.html', context)
        
        # Set new password
        try:
            user.set_password(password1)
            user.save()
            
            # Clear reset token
            user.profile.clear_reset_token()
            
            # Reset failed login attempts (if any)
            user.profile.reset_failed_login_attempts()
            
            # Mark email as verified (user proved email ownership via reset link)
            if not user.profile.email_verified:
                user.profile.mark_email_verified()
            
            messages.success(
                request,
                '✅ Şifreniz başarıyla değiştirildi! Artık yeni şifrenizle giriş yapabilirsiniz.'
            )
            
            # Redirect to login
            return redirect('corpus:login')
            
        except Exception as e:
            messages.error(request, f'❌ Şifre değiştirme sırasında bir hata oluştu: {str(e)}')
            context = {
                'success': True,
                'token': token,
                'user': user,
            }
            return render(request, 'corpus/password_reset_confirm.html', context)
    
    # GET request - show password reset form
    context = {
        'success': True,
        'token': token,
        'user': user,
    }
    return render(request, 'corpus/password_reset_confirm.html', context)


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
    
    export_quota = profile.get_export_quota()
    export_percentage = (profile.export_used_mb / export_quota * 100) if export_quota > 0 else 0
    
    # Compute next query reset date and helper flag for display
    from datetime import date, timedelta
    today = date.today()
    # Next reset is always tomorrow (daily reset at 00:00)
    next_reset_date = today + timedelta(days=1)
    query_reset_is_tomorrow = True

    # Get recent search history (old model)
    recent_searches = request.user.search_history.order_by('-created_at')[:10]
    
    # Get recent query logs (NEW - detailed activity)
    recent_query_logs = QueryLog.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    # Get recent export logs
    recent_export_logs = ExportLog.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'active_tab': 'profile',
        'profile': profile,
        'query_limit': query_limit,
        'query_percentage': query_percentage,
        'export_quota': export_quota,
        'query_reset': next_reset_date,
        'query_reset_is_tomorrow': query_reset_is_tomorrow,
        'export_percentage': export_percentage,
        'recent_searches': recent_searches,
        'recent_query_logs': recent_query_logs,
        'recent_export_logs': recent_export_logs,
    }
    
    return render(request, 'corpus/profile.html', context)


@login_required
def login_history_view(request):
    """Display user's login history for security monitoring (Task 11.15)."""
    from .models import LoginHistory
    from django.core.paginator import Paginator
    
    # Get user's login history
    history = LoginHistory.objects.filter(user=request.user).order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(history, 20)  # 20 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_logins = history.filter(success=True).count()
    failed_attempts = history.filter(success=False).count()
    suspicious_count = history.filter(is_suspicious=True).count()
    
    # Get unique devices/browsers
    unique_devices = history.values('device_type', 'browser', 'os').distinct().count()
    
    # Recent locations (last 10 unique IPs)
    recent_ips = history.values_list('ip_address', flat=True).distinct()[:10]
    
    # Last successful login (excluding current session)
    last_login = history.filter(success=True).exclude(
        session_key=request.session.session_key
    ).first()
    
    context = {
        'active_tab': 'profile',
        'page_obj': page_obj,
        'total_logins': total_logins,
        'failed_attempts': failed_attempts,
        'suspicious_count': suspicious_count,
        'unique_devices': unique_devices,
        'last_login': last_login,
        'recent_ips': recent_ips,
    }
    
    return render(request, 'corpus/login_history.html', context)


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
                # Check filename
                if doc.filename and pattern.search(doc.filename):
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
                similarity=TrigramSimilarity('filename', query) + TrigramSimilarity('author', query)
            ).filter(similarity__gt=0.1).order_by('-similarity')[:10]
        except:
            # Fallback to basic search if PostgreSQL not available
            from django.db.models import Q
            documents = Document.objects.filter(
                Q(filename__icontains=query) |
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
            Q(filename__icontains=query) |
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
            'title': doc.filename,
            'url': f'/corpus/library/?doc={doc.id}',
            'metadata': ' • '.join(metadata_parts),
            'badge': f'{doc.get_word_count()} kelime' if doc.processed else 'İşleniyor',
            'badge_icon': 'article' if doc.processed else 'hourglass_empty'
        })
    
    # Search in collections (only user's collections)
    if request.user.is_authenticated:
        collections = Collection.objects.filter(owner=request.user, name__icontains=query)[:5]
    else:
        collections = Collection.objects.none()
    
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
@login_required
def update_watermark_preference(request):
    """Update user's watermark preference via toggle in profile."""
    if request.method == 'POST':
        profile = request.user.profile
        enable_watermark = request.POST.get('enable_watermark') == 'on'
        
        profile.enable_watermark = enable_watermark
        profile.save()
        
        status = "aktif" if enable_watermark else "devre dışı"
        messages.success(request, f"✅ Filigran tercihi {status} olarak kaydedildi.")
    
    return redirect('corpus:profile')
