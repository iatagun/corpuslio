"""
Dependency Analysis Views

Views for searching and visualizing dependency structures.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from corpus.models import Document
from corpus.permissions import role_required
from corpus.services.dependency_service import DependencyService
from decimal import Decimal
import json


@login_required
@role_required('registered')
def dependency_search_view(request, document_id):
    """
    Main dependency search interface.
    
    Allows users to search for:
    - Dependency relations (nsubj, obj, etc.)
    - Head-dependent pairs
    - Morphological features
    """
    document = get_object_or_404(Document, id=document_id)
    
    # Check if document has dependencies
    if not hasattr(document, 'analysis') or not document.analysis.has_dependencies:
        messages.warning(
            request,
            f"'{document.filename}' henüz bağımlılık ayrıştırması yapılmamış. "
            "CoNLL-U formatında dosya yükleyin veya otomatik ayrıştırma yapın."
        )
        return redirect('corpus:analysis_view', document_id=document_id)
    
    service = DependencyService(document)
    
    # Get search parameters
    search_type = request.GET.get('search_type', 'deprel')
    
    results = []
    statistics = None
    
    try:
        if search_type == 'deprel':
            # Search by dependency relation
            deprel = request.GET.get('deprel', '')
            upos = request.GET.get('upos', '')
            
            if deprel:
                results = service.find_by_deprel(
                    deprel=deprel,
                    upos=upos if upos else None
                )
        
        elif search_type == 'head_dependent':
            # Search for head-dependent pairs
            head_lemma = request.GET.get('head_lemma', '')
            head_pos = request.GET.get('head_pos', '')
            deprel = request.GET.get('deprel', '')
            dependent_pos = request.GET.get('dependent_pos', '')
            
            if head_lemma or head_pos or deprel:
                results = service.find_head_dependent_pairs(
                    head_lemma=head_lemma if head_lemma else None,
                    head_pos=head_pos if head_pos else None,
                    deprel=deprel if deprel else None,
                    dependent_pos=dependent_pos if dependent_pos else None
                )
        
        elif search_type == 'pattern':
            # Pattern search
            pattern = request.GET.get('pattern', '')
            
            if pattern:
                results = service.find_by_pattern(pattern)
        
        elif search_type == 'features':
            # Feature search
            case = request.GET.get('case', '')
            number = request.GET.get('number', '')
            person = request.GET.get('person', '')
            upos = request.GET.get('upos', '')
            
            features = {}
            if case:
                features['Case'] = case
            if number:
                features['Number'] = number
            if person:
                features['Person'] = person
            
            if features:
                results = service.search_by_features(
                    features=features,
                    upos=upos if upos else None
                )
        
        # Get statistics
        statistics = service.get_statistics()
        
    except Exception as e:
        messages.error(request, f"Arama hatası: {str(e)}")
        statistics = {'error': str(e)}
    
    # Common dependency relations for Turkish
    common_deprels = [
        ('nsubj', 'Nominal Subject'),
        ('obj', 'Object'),
        ('iobj', 'Indirect Object'),
        ('obl', 'Oblique Nominal'),
        ('nmod', 'Nominal Modifier'),
        ('amod', 'Adjectival Modifier'),
        ('det', 'Determiner'),
        ('case', 'Case Marking'),
        ('aux', 'Auxiliary'),
        ('cop', 'Copula'),
        ('advmod', 'Adverbial Modifier'),
        ('acl', 'Clausal Modifier of Noun'),
        ('advcl', 'Adverbial Clause Modifier'),
        ('ccomp', 'Clausal Complement'),
        ('xcomp', 'Open Clausal Complement'),
        ('conj', 'Conjunct'),
        ('cc', 'Coordinating Conjunction'),
        ('punct', 'Punctuation'),
        ('root', 'Root'),
    ]
    
    # Common POS tags
    common_pos = [
        'NOUN', 'VERB', 'ADJ', 'ADV', 'PRON',
        'DET', 'ADP', 'NUM', 'CONJ', 'PUNCT'
    ]
    
    # Turkish morphological features
    case_values = ['Nom', 'Acc', 'Dat', 'Loc', 'Abl', 'Gen', 'Ins']
    number_values = ['Sing', 'Plur']
    person_values = ['1', '2', '3']
    
    context = {
        'document': document,
        'search_type': search_type,
        'results': results,
        'result_count': len(results),
        'statistics': statistics,
        'common_deprels': common_deprels,
        'common_pos': common_pos,
        'case_values': case_values,
        'number_values': number_values,
        'person_values': person_values,
        'sentence_count': service.get_sentence_count(),
    }
    
    return render(request, 'corpus/dependency_search.html', context)


@login_required
@role_required('registered')
def dependency_tree_view(request, document_id, sentence_id):
    """
    View single sentence dependency tree.
    
    Returns tree data as JSON for D3.js visualization.
    """
    document = get_object_or_404(Document, id=document_id)
    
    if not hasattr(document, 'analysis') or not document.analysis.has_dependencies:
        return JsonResponse({'error': 'No dependency data available'}, status=404)
    
    service = DependencyService(document)
    
    try:
        tree_data = service.get_sentence_tree(int(sentence_id))
        return JsonResponse(tree_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@role_required('registered')
def dependency_tree_page(request, document_id, sentence_id):
    """
    HTML page for viewing dependency tree visualization.
    """
    document = get_object_or_404(Document, id=document_id)
    
    if not hasattr(document, 'analysis') or not document.analysis.has_dependencies:
        messages.error(request, "Bu belgede bağımlılık verisi bulunmuyor.")
        return redirect('corpus:analysis_view', document_id=document_id)
    
    service = DependencyService(document)
    
    try:
        tree_data = service.get_sentence_tree(int(sentence_id))
        sentence_count = service.get_sentence_count()
    except Exception as e:
        messages.error(request, f"Ağaç verisi alınamadı: {str(e)}")
        return redirect('corpus:dependency_search', document_id=document_id)
    
    context = {
        'document': document,
        'sentence_id': int(sentence_id),
        'sentence_count': sentence_count,
        'tree_data_json': json.dumps(tree_data),
    }
    
    return render(request, 'corpus/dependency_tree.html', context)


@login_required
@role_required('verified_researcher')
def dependency_statistics_view(request, document_id):
    """
    View detailed dependency statistics for a document.
    """
    document = get_object_or_404(Document, id=document_id)
    
    if not hasattr(document, 'analysis') or not document.analysis.has_dependencies:
        messages.error(request, "Bu belgede bağımlılık verisi bulunmuyor.")
        return redirect('corpus:analysis_view', document_id=document_id)
    
    service = DependencyService(document)
    
    try:
        statistics = service.get_statistics()
        deprel_dist = service.get_deprel_distribution()
    except Exception as e:
        messages.error(request, f"İstatistikler alınamadı: {str(e)}")
        return redirect('corpus:dependency_search', document_id=document_id)
    
    context = {
        'document': document,
        'statistics': statistics,
        'deprel_distribution': deprel_dist,
    }
    
    return render(request, 'corpus/dependency_statistics.html', context)
