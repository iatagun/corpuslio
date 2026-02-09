"""Corpus search views using query engine."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from corpus.models import Document
from corpus.query_engine import CorpusQueryEngine
from corpus.collections import Collection as CollectionService
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
    """
    if getattr(request, 'limited', False):
        return render(request, 'corpus/429.html', status=429)
    
    query = request.GET.get('q', '').strip()
    search_type = request.GET.get('type', 'form')  # form, lemma, pos
    regex = request.GET.get('regex', 'false') == 'true'
    case_sensitive = request.GET.get('case', 'false') == 'true'
    context_size = int(request.GET.get('context', 5))
    collection_id = request.GET.get('collection')
    limit = int(request.GET.get('limit', 100))
    
    results = []
    total_matches = 0
    execution_time = 0
    
    if query:
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
        
        total_matches = len(results)
        execution_time = int((time.time() - start_time) * 1000)  # ms
    
    # Get available collections
    collections = CollectionService.objects.all()
    
    context = {
        'query': query,
        'search_type': search_type,
        'regex': regex,
        'case_sensitive': case_sensitive,
        'context_size': context_size,
        'results': results,
        'total_matches': total_matches,
        'execution_time': execution_time,
        'collections': collections,
        'selected_collection': collection_id,
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
