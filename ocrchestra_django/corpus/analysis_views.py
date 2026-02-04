"""Additional corpus analysis views."""

from django.shortcuts import render, get_object_or_404
from .models import Document
from .ngrams import NgramAnalyzer
import json


def ngrams_view(request, doc_id):
    """N-gram and collocation analysis view."""
    document = get_object_or_404(Document, id=doc_id)
    
    if not document.processed or not hasattr(document, 'analysis'):
        from django.contrib import messages
        messages.error(request, 'Bu belge henüz analiz edilmedi.')
        from django.shortcuts import redirect
        return redirect('corpus:library')
    
    analyzer = NgramAnalyzer(document.analysis.data)
    
    # Get n-gram type from query params
    ngram_type = request.GET.get('type', 'bigram')
    n = 2 if ngram_type == 'bigram' else 3
    
    # Get n-grams
    top_ngrams = analyzer.get_top_ngrams(n=n, top_k=50)
    
    # Get POS patterns
    pos_patterns = analyzer.get_ngram_pos_patterns(n=n, top_k=30)
    
    # Collocation search
    collocations = []
    search_word = request.GET.get('word', '')
    if search_word:
        collocations = analyzer.find_collocations(search_word, top_k=20)
    
    context = {
        'document': document,
        'ngram_type': ngram_type,
        'top_ngrams': top_ngrams,
        'pos_patterns': pos_patterns,
        'collocations': collocations,
        'search_word': search_word,
        'active_tab': 'analysis'
    }
    return render(request, 'corpus/ngrams.html', context)


def wordcloud_view(request, doc_id):
    """Word cloud and frequency visualization."""
    document = get_object_or_404(Document, id=doc_id)
    
    if not document.processed or not hasattr(document, 'analysis'):
        from django.contrib import messages
        messages.error(request, 'Bu belge henüz analiz edilmedi.')
        from django.shortcuts import redirect
        return redirect('corpus:library')
    
    from collections import Counter
    
    # Get word frequencies
    words = [item.get('word', '').lower() for item in document.analysis.data if isinstance(item, dict)]
    word_freq = dict(Counter(words).most_common(100))
    
    # Get lemma frequencies
    lemmas = [item.get('lemma', '').lower() for item in document.analysis.data if isinstance(item, dict) and item.get('lemma')]
    lemma_freq = dict(Counter(lemmas).most_common(100))
    
    # Prepare data for Plotly
    context = {
        'document': document,
        'word_freq': json.dumps(word_freq),
        'lemma_freq': json.dumps(lemma_freq),
        'active_tab': 'analysis'
    }
    return render(request, 'corpus/wordcloud.html', context)
