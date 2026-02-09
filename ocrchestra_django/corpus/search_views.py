"""Corpus search views using query engine."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from corpus.models import Document
from corpus.query_engine import CorpusQueryEngine
from corpus.collections import Collection as CollectionService
from corpus.corpus_export_utils import (
    export_concordance_csv, export_concordance_json,
    export_collocation_csv, export_ngram_csv, export_frequency_csv
)
import time


@ratelimit(key='user_or_ip', rate='100/h', method='GET')
def corpus_search_view(request):
    """Main corpus search interface with linguistic features.
    
    Supports:
    - KWIC concordance
    - Regex on forms/lemmas
    - POS filtering
    - Pattern matching
    - Collection filtering
    - Genre/Author filtering
    """
    if getattr(request, 'limited', False):
        return render(request, 'corpus/429.html', status=429)
    
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'form')  # form, lemma, pos
    regex = request.GET.get('regex', 'false') == 'true'
    case_sensitive = request.GET.get('case', 'false') == 'true'
    context_size = int(request.GET.get('context', 5))
    collection_id = request.GET.get('collection')
    genre_filter = request.GET.get('genre')
    author_filter = request.GET.get('author')
    sort_by = request.GET.get('sort', 'none')  # none, left, right, frequency
    limit = int(request.GET.get('limit', 100))
    
    results = []
    total_matches = 0
    execution_time = 0
    unique_docs = 0
    
    if query:
        import time
        start_time = time.time()
        
        # Filter by collection, genre, author
        document_ids = None
        from corpus.models import CorpusMetadata
        
        filter_kwargs = {}
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        # Filter by genre/author
        if genre_filter or author_filter:
            meta_query = CorpusMetadata.objects.all()
            if genre_filter:
                meta_query = meta_query.filter(global_metadata__genre__icontains=genre_filter)
            if author_filter:
                meta_query = meta_query.filter(global_metadata__author__icontains=author_filter)
            
            meta_doc_ids = list(meta_query.values_list('document_id', flat=True))
            
            if document_ids:
                # Intersection with collection
                document_ids = list(set(document_ids) & set(meta_doc_ids))
            else:
                document_ids = meta_doc_ids
        
        # Initialize query engine
        engine = CorpusQueryEngine(documents=document_ids)
        
        # Execute concordance search
        results = engine.concordance(
            query=query,
            context_size=context_size,
            query_type=search_type,
            regex=regex,
            case_sensitive=case_sensitive,
            limit=limit
        )
        
        # Sorting
        if sort_by == 'left':
            results.sort(key=lambda x: x.get('left', '').lower())
        elif sort_by == 'right':
            results.sort(key=lambda x: x.get('right', '').lower())
        elif sort_by == 'document':
            results.sort(key=lambda x: x.get('document', ''))
        
        total_matches = len(results)
        unique_docs = len(set(r.get('document', '') for r in results))
        execution_time = int((time.time() - start_time) * 1000)  # ms
    
    # Get available collections, genres, authors
    collections = CollectionService.objects.all()
    
    # Get unique genres and authors from CorpusMetadata.global_metadata JSONField
    from corpus.models import CorpusMetadata
    
    genres = set()
    authors = set()
    
    for metadata in CorpusMetadata.objects.all():
        if metadata.global_metadata:
            if 'genre' in metadata.global_metadata and metadata.global_metadata['genre']:
                genres.add(metadata.global_metadata['genre'])
            if 'author' in metadata.global_metadata and metadata.global_metadata['author']:
                authors.add(metadata.global_metadata['author'])
    
    genres = sorted(genres)
    authors = sorted(authors)
    
    context = {
        'query': query,
        'search_type': search_type,
        'regex': regex,
        'case_sensitive': case_sensitive,
        'context_size': context_size,
        'results': results,
        'total_matches': total_matches,
        'unique_docs': unique_docs,
        'execution_time': execution_time,
        'collections': collections,
        'selected_collection': collection_id,
        'genres': genres,
        'authors': authors,
        'selected_genre': genre_filter,
        'selected_author': author_filter,
        'sort_by': sort_by,
        'active_tab': 'search',
    }
    
    return render(request, 'corpus/corpus_search.html', context)


@ratelimit(key='user_or_ip', rate='50/h', method='GET')
def collocation_view(request):
    """Collocation analysis view."""
    if getattr(request, 'limited', False):
        return render(request, 'corpus/429.html', status=429)
    
    keyword = request.GET.get('keyword', '').strip()
    window_size = int(request.GET.get('window', 5))
    min_freq = int(request.GET.get('min_freq', 2))
    collection_id = request.GET.get('collection')
    
    collocates = []
    execution_time = 0
    
    if keyword:
        import time
        start_time = time.time()
        
        # Filter by collection
        document_ids = None
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        engine = CorpusQueryEngine(documents=document_ids)
        collocates = engine.collocation(
            keyword=keyword,
            window_size=window_size,
            min_frequency=min_freq
        )
        
        execution_time = int((time.time() - start_time) * 1000)
    
    # Get available collections
    collections = CollectionService.objects.all()
    
    context = {
        'keyword': keyword,
        'window_size': window_size,
        'min_freq': min_freq,
        'collocates': collocates[:50],  # Top 50
        'total_collocates': sum(c['frequency'] for c in collocates[:50]),
        'execution_time': execution_time,
        'collections': collections,
        'active_tab': 'statistics',
    }
    
    return render(request, 'corpus/collocation.html', context)


@ratelimit(key='user_or_ip', rate='50/h', method='GET')
def ngram_view(request):
    """N-gram analysis view."""
    if getattr(request, 'limited', False):
        return render(request, 'corpus/429.html', status=429)
    
    n = int(request.GET.get('n', 2))
    min_freq = int(request.GET.get('min_freq', 2))
    use_lemma = request.GET.get('use_lemma', 'true') == 'true'
    collection_id = request.GET.get('collection')
    limit = int(request.GET.get('limit', 100))
    
    ngrams = []
    execution_time = 0
    
    if request.GET.get('analyze'):
        import time
        start_time = time.time()
        
        # Filter by collection
        document_ids = None
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        engine = CorpusQueryEngine(documents=document_ids)
        ngrams = engine.ngrams(
            n=n,
            min_frequency=min_freq,
            use_lemma=use_lemma,
            limit=limit
        )
        
        execution_time = int((time.time() - start_time) * 1000)
    
    # Get available collections
    collections = CollectionService.objects.all()
    
    context = {
        'n': n,
        'min_freq': min_freq,
        'use_lemma': use_lemma,
        'ngrams': ngrams,
        'total_ngrams': len(ngrams),
        'execution_time': execution_time,
        'collections': collections,
        'active_tab': 'statistics',
    }
    
    return render(request, 'corpus/ngram.html', context)


@ratelimit(key='user_or_ip', rate='50/h', method='GET')
def frequency_view(request):
    """Word frequency analysis view."""
    if getattr(request, 'limited', False):
        return render(request, 'corpus/429.html', status=429)
    
    use_lemma = request.GET.get('use_lemma', 'true') == 'true'
    min_length = int(request.GET.get('min_length', 1))
    collection_id = request.GET.get('collection')
    limit = int(request.GET.get('limit', 100))
    
    frequencies = []
    pos_dist = {}
    execution_time = 0
    
    if request.GET.get('analyze'):
        import time
        start_time = time.time()
        
        # Filter by collection
        document_ids = None
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        engine = CorpusQueryEngine(documents=document_ids)
        
        # Word frequency
        frequencies = engine.word_frequency(
            use_lemma=use_lemma,
            limit=limit,
            min_length=min_length
        )
        
        # POS distribution
        pos_dist = engine.pos_distribution()
        
        execution_time = int((time.time() - start_time) * 1000)
    
    # Get available collections
    collections = CollectionService.objects.all()
    
    context = {
        'use_lemma': use_lemma,
        'min_length': min_length,
        'frequencies': frequencies,
        'pos_distribution': pos_dist,
        'execution_time': execution_time,
        'collections': collections,
        'active_tab': 'statistics',
    }
    
    return render(request, 'corpus/frequency.html', context)


@require_http_methods(['GET'])
def api_concordance(request):
    """JSON API for concordance search."""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'error': 'Query required'}, status=400)
    
    search_type = request.GET.get('type', 'form')
    regex = request.GET.get('regex', 'false') == 'true'
    limit = min(int(request.GET.get('limit', 50)), 500)
    
    engine = CorpusQueryEngine()
    results = engine.concordance(
        query=query,
        query_type=search_type,
        regex=regex,
        limit=limit
    )
    
    return JsonResponse({
        'query': query,
        'total': len(results),
        'results': results
    })


# Export Views

@login_required
def export_concordance_view(request):
    """Export KWIC concordance search results."""
    query = request.GET.get('q', '').strip()
    export_format = request.GET.get('format', 'csv')  # csv or json
    
    if not query:
        return JsonResponse({'error': 'Query required'}, status=400)
    
    # Get search parameters (same as corpus_search_view)
    search_type = request.GET.get('type', 'form')
    regex = request.GET.get('regex', 'false') == 'true'
    case_sensitive = request.GET.get('case', 'false') == 'true'
    context_size = int(request.GET.get('context', 5))
    collection_id = request.GET.get('collection')
    genre_filter = request.GET.get('genre')
    author_filter = request.GET.get('author')
    limit = int(request.GET.get('limit', 500))
    
    # Filter by collection, genre, author
    document_ids = None
    from corpus.models import CorpusMetadata
    
    if collection_id:
        try:
            collection = CollectionService.objects.get(id=collection_id)
            document_ids = list(collection.documents.values_list('id', flat=True))
        except:
            pass
    
    # Filter by genre/author
    if genre_filter or author_filter:
        meta_query = CorpusMetadata.objects.all()
        if genre_filter:
            meta_query = meta_query.filter(global_metadata__genre__icontains=genre_filter)
        if author_filter:
            meta_query = meta_query.filter(global_metadata__author__icontains=author_filter)
        
        meta_doc_ids = list(meta_query.values_list('document_id', flat=True))
        
        if document_ids:
            # Intersection with collection
            document_ids = list(set(document_ids) & set(meta_doc_ids))
        else:
            document_ids = meta_doc_ids
    
    # Execute search
    engine = CorpusQueryEngine(documents=document_ids)
    results = engine.concordance(
        query=query,
        context_size=context_size,
        query_type=search_type,
        regex=regex,
        case_sensitive=case_sensitive,
        limit=limit
    )
    
    # Export
    if export_format == 'json':
        return export_concordance_json(results, query, request.user)
    else:
        return export_concordance_csv(results, query, request.user)


@login_required
def export_collocation_view(request):
    """Export collocation analysis results."""
    keyword = request.GET.get('keyword', '').strip()
    
    if not keyword:
        return JsonResponse({'error': 'Keyword required'}, status=400)
    
    window_size = int(request.GET.get('window', 5))
    min_freq = int(request.GET.get('min_freq', 2))
    collection_id = request.GET.get('collection')
    
    # Filter by collection
    document_ids = None
    if collection_id:
        try:
            collection = CollectionService.objects.get(id=collection_id)
            document_ids = list(collection.documents.values_list('id', flat=True))
        except:
            pass
    
    # Execute analysis
    engine = CorpusQueryEngine(documents=document_ids)
    collocates = engine.collocation(
        keyword=keyword,
        window_size=window_size,
        min_frequency=min_freq
    )
    
    return export_collocation_csv(collocates[:100], keyword, request.user)


@login_required
def export_ngram_view(request):
    """Export n-gram analysis results."""
    n = int(request.GET.get('n', 2))
    min_freq = int(request.GET.get('min_freq', 2))
    use_lemma = request.GET.get('use_lemma', 'true') == 'true'
    collection_id = request.GET.get('collection')
    limit = int(request.GET.get('limit', 500))
    
    # Filter by collection
    document_ids = None
    if collection_id:
        try:
            collection = CollectionService.objects.get(id=collection_id)
            document_ids = list(collection.documents.values_list('id', flat=True))
        except:
            pass
    
    # Execute analysis
    engine = CorpusQueryEngine(documents=document_ids)
    ngrams = engine.ngrams(
        n=n,
        min_frequency=min_freq,
        use_lemma=use_lemma,
        limit=limit
    )
    
    return export_ngram_csv(ngrams, n, request.user)


@login_required
def export_frequency_view(request):
    """Export word frequency analysis results."""
    use_lemma = request.GET.get('use_lemma', 'true') == 'true'
    min_length = int(request.GET.get('min_length', 1))
    collection_id = request.GET.get('collection')
    limit = int(request.GET.get('limit', 500))
    
    # Filter by collection
    document_ids = None
    if collection_id:
        try:
            collection = CollectionService.objects.get(id=collection_id)
            document_ids = list(collection.documents.values_list('id', flat=True))
        except:
            pass
    
    # Execute analysis
    engine = CorpusQueryEngine(documents=document_ids)
    frequencies = engine.word_frequency(
        use_lemma=use_lemma,
        limit=limit,
        min_length=min_length
    )
    
    return export_frequency_csv(frequencies, request.user)
