"""Additional corpus analysis views."""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Document
from .ngrams import NgramAnalyzer
import json


@login_required
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


@login_required
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


@login_required
def comparison_view(request):
    """Compare two documents side by side."""
    from collections import Counter
    from django.http import JsonResponse
    
    # Get document IDs from query params
    doc1_id = request.GET.get('doc1')
    doc2_id = request.GET.get('doc2')
    
    # Get all processed documents for selection
    documents = Document.objects.filter(processed=True).order_by('-upload_date')
    
    comparison_data = None
    doc1 = None
    doc2 = None
    
    if doc1_id and doc2_id:
        doc1 = get_object_or_404(Document, id=doc1_id, processed=True)
        doc2 = get_object_or_404(Document, id=doc2_id, processed=True)
        
        # Get analysis data
        data1 = doc1.analysis.data if hasattr(doc1, 'analysis') else []
        data2 = doc2.analysis.data if hasattr(doc2, 'analysis') else []
        
        # Extract words and lemmas
        words1 = [item.get('word', '').lower() for item in data1 if isinstance(item, dict)]
        words2 = [item.get('word', '').lower() for item in data2 if isinstance(item, dict)]
        
        lemmas1 = [item.get('lemma', '').lower() for item in data1 if isinstance(item, dict) and item.get('lemma')]
        lemmas2 = [item.get('lemma', '').lower() for item in data2 if isinstance(item, dict) and item.get('lemma')]
        
        # POS tags
        pos1 = [item.get('pos', '') for item in data1 if isinstance(item, dict) and item.get('pos')]
        pos2 = [item.get('pos', '') for item in data2 if isinstance(item, dict) and item.get('pos')]
        
        # Calculate statistics
        word_freq1 = Counter(words1)
        word_freq2 = Counter(words2)
        lemma_freq1 = Counter(lemmas1)
        lemma_freq2 = Counter(lemmas2)
        pos_freq1 = Counter(pos1)
        pos_freq2 = Counter(pos2)
        
        # Find common and unique words
        common_words = set(words1) & set(words2)
        unique_words1 = set(words1) - set(words2)
        unique_words2 = set(words2) - set(words1)
        
        # Find common and unique lemmas
        common_lemmas = set(lemmas1) & set(lemmas2)
        unique_lemmas1 = set(lemmas1) - set(lemmas2)
        unique_lemmas2 = set(lemmas2) - set(lemmas1)
        
        # Top common words by total frequency
        common_word_freq = {word: word_freq1[word] + word_freq2[word] 
                           for word in common_words}
        top_common_words = dict(Counter(common_word_freq).most_common(30))
        
        # Top unique words
        top_unique_words1 = dict(Counter({w: word_freq1[w] for w in unique_words1}).most_common(20))
        top_unique_words2 = dict(Counter({w: word_freq2[w] for w in unique_words2}).most_common(20))
        
        comparison_data = {
            'basic_stats': {
                'doc1': {
                    'total_words': len(words1),
                    'unique_words': len(set(words1)),
                    'unique_lemmas': len(set(lemmas1)),
                    'pos_tags': len(pos1)
                },
                'doc2': {
                    'total_words': len(words2),
                    'unique_words': len(set(words2)),
                    'unique_lemmas': len(set(lemmas2)),
                    'pos_tags': len(pos2)
                }
            },
            'similarity': {
                'common_words': len(common_words),
                'common_lemmas': len(common_lemmas),
                'jaccard_words': len(common_words) / len(set(words1) | set(words2)) if (set(words1) | set(words2)) else 0,
                'jaccard_lemmas': len(common_lemmas) / len(set(lemmas1) | set(lemmas2)) if (set(lemmas1) | set(lemmas2)) else 0
            },
            'differences': {
                'unique_words1': len(unique_words1),
                'unique_words2': len(unique_words2),
                'unique_lemmas1': len(unique_lemmas1),
                'unique_lemmas2': len(unique_lemmas2)
            },
            'top_common_words': top_common_words,
            'top_unique_words1': top_unique_words1,
            'top_unique_words2': top_unique_words2,
            'pos_distribution1': dict(pos_freq1.most_common(10)),
            'pos_distribution2': dict(pos_freq2.most_common(10))
        }
    
    context = {
        'documents': documents,
        'doc1': doc1,
        'doc2': doc2,
        'comparison_data': json.dumps(comparison_data) if comparison_data else None,
        'active_tab': 'comparison'
    }
    
    return render(request, 'corpus/comparison.html', context)
