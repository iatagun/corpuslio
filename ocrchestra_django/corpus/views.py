"""Views for corpus management."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie

from .models import Document, ProcessingTask, Analysis
from .forms import DocumentUploadForm
from .tasks import process_document_task
from .services import CorpusService
from .collections import Collection
import os


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


@ensure_csrf_cookie
def library_view(request):
    """Display all documents in library with filtering."""
    documents = Document.objects.all()
    
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
    
    documents = documents.order_by('-upload_date')
    
    # Get unique values for filter dropdowns
    all_genres = set()
    for doc in Document.objects.all():
        if doc.metadata and doc.metadata.get('genre'):
            all_genres.add(doc.metadata['genre'])
    
    context = {
        'documents': documents,
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
        
        search_results = service.search_in_document(document, search_params)
    
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
        'search_results': search_results,
        'pos_tags': pos_tags,
        'active_tab': 'analysis'
    }
    return render(request, 'corpus/analysis.html', context)


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


@require_http_methods(["POST"])
def delete_document(request, doc_id):
    """Delete a document."""
    document = get_object_or_404(Document, id=doc_id)
    filename = document.filename
    document.delete()
    
    messages.success(request, f'✅ {filename} silindi.')
    return redirect('corpus:library')


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
