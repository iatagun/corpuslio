"""Advanced search views with CQP-style pattern matching support."""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from .models import Document, QueryLog
from .permissions import role_required
from .validators import validate_cqp_query as validate_query, validate_integer_param
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from corpuslio.query_parser import CQPQueryParser, PatternMatcher, parse_cqp_query


@login_required
@role_required('researcher')
@ratelimit(key='user', rate='50/hour', method='POST', block=True)
def advanced_search_view(request):
    """Advanced search with CQP-style pattern matching.
    
    Supports:
    - [word="pattern"] - word matching
    - [lemma="pattern"] - lemma matching
    - [pos="TAG"] - POS tag matching
    - [word="pattern" & pos="TAG"] - multiple constraints
    - [pos="ADJ"] [pos="NOUN"] - sequence patterns
    """
    context = {
        'active_tab': 'search',
        'query': '',
        'results': [],
        'total_matches': 0,
        'query_type': 'cqp',
        'examples': [
            {'query': '[word="test"]', 'description': 'Find exact word "test"'},
            {'query': '[pos="NOUN"]', 'description': 'Find all nouns'},
            {'query': '[pos="ADJ"] [pos="NOUN"]', 'description': 'Find adjective + noun sequences'},
            {'query': '[word=".*ing"]', 'description': 'Find words ending in "ing" (regex)'},
            {'query': '[lemma="git.*"]', 'description': 'Find lemmas starting with "git"'},
            {'query': '[word="test" & pos="NOUN"]', 'description': 'Find "test" as a noun'},
        ]
    }
    
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        document_id = request.POST.get('document_id')
        context_size_raw = request.POST.get('context_size', '5')
        
        if not query:
            messages.error(request, "Please enter a search query")
            return render(request, 'corpus/advanced_search.html', context)
        
        # Validate query input
        try:
            validate_query(query)
        except ValidationError as e:
            messages.error(request, f"Invalid query: {e.message}")
            return render(request, 'corpus/advanced_search.html', context)
        
        # Validate context_size parameter
        try:
            context_size = validate_integer_param(context_size_raw, min_value=1, max_value=20, param_name='context_size')
        except ValidationError as e:
            messages.error(request, str(e))
            context_size = 5  # Default fallback
        
        context['query'] = query
        context['context_size'] = context_size
        
        # Parse CQP query
        parser = CQPQueryParser()
        pattern = parser.parse(query)
        
        if pattern is None:
            messages.error(request, f"Invalid query syntax: {parser.last_error}")
            context['error'] = parser.last_error
            return render(request, 'corpus/advanced_search.html', context)
        
        # Get query info for display
        query_info = parser.get_query_info(query)
        context['query_info'] = query_info
        
        # Search in document(s)
        if document_id:
            # Search in specific document
            documents = [get_object_or_404(Document, id=document_id, processed=True)]
        else:
            # Search in all accessible documents
            if request.user.is_superuser:
                documents = Document.objects.filter(processed=True)
            else:
                documents = Document.objects.filter(
                    processed=True,
                    uploaded_by=request.user
                )
        
        all_matches = []
        matcher = PatternMatcher()
        
        for doc in documents:
            # Get document analysis
            if not doc.analysis or not doc.analysis.get('tokens'):
                continue
            
            tokens = doc.analysis.get('tokens', [])
            
            # Normalize tokens if needed
            if tokens and not isinstance(tokens[0], dict):
                # Convert flat list to dict format
                normalized_tokens = []
                i = 0
                while i < len(tokens):
                    if i + 2 < len(tokens):
                        normalized_tokens.append({
                            'word': tokens[i],
                            'lemma': tokens[i+1],
                            'pos': tokens[i+2]
                        })
                    i += 3
                tokens = normalized_tokens
            
            # Find matches in this document
            matches = matcher.find_matches(pattern, tokens, context_size)
            
            # Add document info to each match
            for match in matches:
                match['document'] = {
                    'id': doc.id,
                    'title': doc.title if hasattr(doc, 'title') else doc.filename,
                    'filename': doc.filename
                }
                all_matches.append(match)
        
        context['results'] = all_matches
        context['total_matches'] = len(all_matches)
        context['document_count'] = len(documents)
        
        # Log query
        QueryLog.objects.create(
            user=request.user,
            query=query,
            query_type='cqp_advanced',
            results_count=len(all_matches),
            timestamp=timezone.now()
        )
        
        if len(all_matches) > 0:
            messages.success(request, f"Found {len(all_matches)} matches in {len(documents)} document(s)")
        else:
            messages.warning(request, "No matches found")
    
    return render(request, 'corpus/advanced_search.html', context)


@require_http_methods(["POST"])
@login_required
@ratelimit(key='user', rate='100/hour', method='POST', block=True)
def validate_cqp_query(request):
    """AJAX endpoint to validate CQP query syntax.
    
    Returns JSON with validation result.
    """
    query = request.POST.get('query', '').strip()
    
    if not query:
        return JsonResponse({
            'valid': False,
            'error': 'Empty query'
        })
    
    # First, validate with security validator
    try:
        validate_query(query)
    except ValidationError as e:
        return JsonResponse({
            'valid': False,
            'error': str(e.message)
        })
    
    # Then, validate CQP syntax
    parser = CQPQueryParser()
    is_valid, error = parser.validate_query(query)
    
    if is_valid:
        query_info = parser.get_query_info(query)
        return JsonResponse({
            'valid': True,
            'info': query_info
        })
    else:
        return JsonResponse({
            'valid': False,
            'error': error
        })


@login_required
def query_syntax_help(request):
    """Query syntax tutorial and help page."""
    
    examples = [
        {
            'category': 'Basic Token Matching',
            'items': [
                {
                    'query': '[word="test"]',
                    'description': 'Find exact word "test"',
                    'matches': 'test',
                    'not_matches': 'Test, testing, tests'
                },
                {
                    'query': '[lemma="git"]',
                    'description': 'Find all forms of lemma "git" (go)',
                    'matches': 'gitti, gidiyor, gidecek',
                    'not_matches': 'geldi, gelecek'
                },
                {
                    'query': '[pos="NOUN"]',
                    'description': 'Find all nouns',
                    'matches': 'ev, kitap, masa',
                    'not_matches': 'güzel (ADJ), koştu (VERB)'
                }
            ]
        },
        {
            'category': 'Regex Patterns',
            'items': [
                {
                    'query': '[word=".*lik"]',
                    'description': 'Words ending with "lik"',
                    'matches': 'güzellik, sevgilik, dostluk',
                    'not_matches': 'güzel, sevgi'
                },
                {
                    'query': '[word="test.*"]',
                    'description': 'Words starting with "test"',
                    'matches': 'test, testing, tested',
                    'not_matches': 'contest, retest'
                },
                {
                    'query': '[lemma="[aeiou].*"]',
                    'description': 'Lemmas starting with vowel',
                    'matches': 'at, et, it, ok',
                    'not_matches': 'git, kal, ver'
                }
            ]
        },
        {
            'category': 'Multiple Constraints',
            'items': [
                {
                    'query': '[word="test" & pos="NOUN"]',
                    'description': '"test" as a noun only',
                    'matches': 'test (when used as noun)',
                    'not_matches': 'test (when used as verb)'
                },
                {
                    'query': '[lemma="büyük" & pos="ADJ"]',
                    'description': 'Lemma "büyük" as adjective',
                    'matches': 'büyük, büyüğü (as adjective)',
                    'not_matches': 'büyük (when noun)'
                }
            ]
        },
        {
            'category': 'Sequence Patterns',
            'items': [
                {
                    'query': '[pos="ADJ"] [pos="NOUN"]',
                    'description': 'Adjective followed by noun',
                    'matches': 'güzel ev, büyük kitap',
                    'not_matches': 'ev güzel, kitap büyük'
                },
                {
                    'query': '[pos="DET"] [pos="ADJ"] [pos="NOUN"]',
                    'description': 'Determiner + Adjective + Noun',
                    'matches': 'bir güzel ev, o büyük kitap',
                    'not_matches': 'güzel ev, büyük kitap'
                },
                {
                    'query': '[pos="VERB"] [lemma="ve"] [pos="VERB"]',
                    'description': 'Two verbs connected by "ve" (and)',
                    'matches': 'geldi ve gitti, okudu ve yazdı',
                    'not_matches': 'geldi veya gitti'
                }
            ]
        },
        {
            'category': 'Advanced Examples',
            'items': [
                {
                    'query': '[word=".*mak"] [pos="AUX"]',
                    'description': 'Infinitive verb + auxiliary',
                    'matches': 'yapmak istiyorum, gelmek zorundayım',
                    'not_matches': 'yaptı, geldi'
                },
                {
                    'query': '[pos="NOUN"] [lemma="için"]',
                    'description': 'Noun followed by "için" (for)',
                    'matches': 'sen için, ev için',
                    'not_matches': 'için geldi'
                }
            ]
        }
    ]
    
    context = {
        'active_tab': 'help',
        'examples': examples,
        'attributes': [
            {
                'name': 'word',
                'description': 'Surface form of the word',
                'example': '[word="test"]'
            },
            {
                'name': 'lemma',
                'description': 'Base/dictionary form',
                'example': '[lemma="gitmek"]'
            },
            {
                'name': 'pos',
                'description': 'Part-of-speech tag',
                'example': '[pos="NOUN"]'
            }
        ],
        'operators': [
            {
                'symbol': '&',
                'description': 'AND - combine multiple constraints',
                'example': '[word="test" & pos="NOUN"]'
            },
            {
                'symbol': '.*',
                'description': 'Regex: match any characters',
                'example': '[word="test.*"]'
            },
            {
                'symbol': '^',
                'description': 'Regex: start of string',
                'example': '[word="^test"]'
            },
            {
                'symbol': '$',
                'description': 'Regex: end of string',
                'example': '[word="test$"]'
            }
        ]
    }
    
    return render(request, 'corpus/query_syntax_help.html', context)
