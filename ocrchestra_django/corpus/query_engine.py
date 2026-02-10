"""Corpus Query Engine - CQP-like search for linguistic corpora.

Supports:
- KWIC concordance (Key Word In Context)
- Regex on forms, lemmas
- POS pattern matching
- Morphological feature filtering
- Dependency relation queries
- Collocation analysis
"""

import re
from typing import List, Dict, Optional, Tuple
from django.db.models import Q, Count, F
from corpus.models import Token, Sentence, Document


class CorpusQueryEngine:
    """Query engine for linguistic corpus search."""
    
    def __init__(self, documents: Optional[List[int]] = None):
        """Initialize query engine.
        
        Args:
            documents: List of document IDs to search in (None = all)
        """
        self.documents = documents
        self.base_queryset = Token.objects.all()
        
        if documents:
            self.base_queryset = self.base_queryset.filter(document_id__in=documents)
    
    def concordance(
        self, 
        query: str,
        context_size: int = 5,
        query_type: str = 'form',
        regex: bool = False,
        case_sensitive: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """KWIC concordance search.
        
        Args:
            query: Search term
            context_size: Number of tokens on each side (default 5)
            query_type: 'form', 'lemma', 'upos' (default 'form')
            regex: Use regex matching (default False)
            case_sensitive: Case-sensitive search (default False)
            limit: Max results (default 100)
        
        Returns:
            List of concordance lines with left/right context
        """
        # Build query
        if query_type == 'form':
            field = 'form'
        elif query_type == 'lemma':
            field = 'lemma'
        elif query_type == 'upos':
            field = 'upos'
        else:
            field = 'form'
        
        # Apply filters
        if regex:
            if case_sensitive:
                filter_kwargs = {f'{field}__regex': query}
            else:
                filter_kwargs = {f'{field}__iregex': query}
        else:
            if case_sensitive:
                filter_kwargs = {f'{field}__exact': query}
            else:
                filter_kwargs = {f'{field}__iexact': query}
        
        matching_tokens = self.base_queryset.filter(
            **filter_kwargs
        ).select_related('sentence', 'document')[:limit]
        
        results = []
        for token in matching_tokens:
            # Get context tokens
            sent_tokens = Token.objects.filter(
                sentence=token.sentence
            ).order_by('index')
            
            left_context = []
            keyword = None
            right_context = []
            
            for t in sent_tokens:
                if t.index < token.index:
                    left_context.append(t.form)
                elif t.index == token.index:
                    keyword = t.form
                else:
                    right_context.append(t.form)
            
            # Trim context
            left_context = left_context[-context_size:] if left_context else []
            right_context = right_context[:context_size] if right_context else []
            
            results.append({
                'left': ' '.join(left_context),
                'keyword': keyword,
                'right': ' '.join(right_context),
                'document': token.document.filename,
                'sentence_id': token.sentence.id,
                'sentence_index': token.sentence.index,
                'token_id': token.id,
                'lemma': token.lemma,
                'pos': token.upos,
            })
        
        return results
    
    def pattern_search(
        self,
        pattern: str,
        limit: int = 100
    ) -> List[Dict]:
        """CQP-style pattern search.
        
        Pattern syntax:
        - [lemma="git.*"] - regex on lemma
        - [pos="VERB"] - exact POS match
        - [lemma="git" & pos="VERB"] - combined conditions
        - [word=".*yor$"] - regex on word form
        
        Args:
            pattern: CQP-style pattern
            limit: Max results
        
        Returns:
            List of matches with context
        """
        # Parse pattern
        conditions = self._parse_pattern(pattern)
        
        # Build query
        query = Q()
        for field, value, is_regex in conditions:
            if is_regex:
                query &= Q(**{f'{field}__iregex': value})
            else:
                query &= Q(**{f'{field}__iexact': value})
        
        matching_tokens = self.base_queryset.filter(query)[:limit]
        
        results = []
        for token in matching_tokens:
            results.append({
                'form': token.form,
                'lemma': token.lemma,
                'pos': token.upos,
                'sentence': token.sentence.text,
                'document': token.document.filename,
            })
        
        return results
    
    def _parse_pattern(self, pattern: str) -> List[Tuple[str, str, bool]]:
        """Parse CQP-style pattern.
        
        Args:
            pattern: Pattern string like [lemma="git.*" & pos="VERB"]
        
        Returns:
            List of (field, value, is_regex) tuples
        """
        # Remove brackets
        pattern = pattern.strip('[]')
        
        # Split by &
        parts = pattern.split('&')
        
        conditions = []
        for part in parts:
            part = part.strip()
            
            # Parse field="value"
            match = re.match(r'(\w+)="([^"]+)"', part)
            if match:
                field_alias, value = match.groups()
                
                # Map aliases to model fields
                field_map = {
                    'word': 'form',
                    'lemma': 'lemma',
                    'pos': 'upos',
                    'tag': 'upos',
                }
                field = field_map.get(field_alias, field_alias)
                
                # Check if regex
                is_regex = bool(re.search(r'[.*+?^$]', value))
                
                conditions.append((field, value, is_regex))
        
        return conditions
    
    def collocation(
        self,
        keyword: str,
        window_size: int = 5,
        min_frequency: int = 2,
        measure: str = 'frequency'
    ) -> List[Dict]:
        """Collocation analysis.
        
        Args:
            keyword: Target word
            window_size: Context window (default 5)
            min_frequency: Minimum co-occurrence (default 2)
            measure: 'frequency', 'mi' (mutual information)
        
        Returns:
            List of collocates with statistics
        """
        # Find keyword tokens
        keyword_tokens = self.base_queryset.filter(
            lemma__iexact=keyword
        ).select_related('sentence')
        
        # Collect collocates
        collocates = {}
        
        for kw_token in keyword_tokens:
            # Get context tokens
            sent_tokens = Token.objects.filter(
                sentence=kw_token.sentence
            ).order_by('index')
            
            for token in sent_tokens:
                # Skip keyword itself and punctuation
                if token.id == kw_token.id or token.upos == 'PUNCT':
                    continue
                
                # Check if in window
                distance = abs(token.index - kw_token.index)
                if distance <= window_size:
                    collocate = token.lemma.lower()
                    
                    if collocate not in collocates:
                        collocates[collocate] = {
                            'lemma': collocate,
                            'frequency': 0,
                            'positions': {'left': 0, 'right': 0},
                        }
                    
                    collocates[collocate]['frequency'] += 1
                    
                    if token.index < kw_token.index:
                        collocates[collocate]['positions']['left'] += 1
                    else:
                        collocates[collocate]['positions']['right'] += 1
        
        # Filter by min frequency
        results = [
            col for col in collocates.values()
            if col['frequency'] >= min_frequency
        ]
        
        # Sort by frequency
        results.sort(key=lambda x: x['frequency'], reverse=True)
        
        return results
    
    def ngrams(
        self,
        n: int = 2,
        min_frequency: int = 2,
        use_lemma: bool = False,
        limit: int = 100
    ) -> List[Dict]:
        """N-gram extraction.
        
        Args:
            n: N-gram size (2=bigram, 3=trigram)
            min_frequency: Minimum occurrence
            use_lemma: Use lemmas instead of forms
            limit: Max results
        
        Returns:
            List of n-grams with frequencies
        """
        # Get all sentences
        if self.documents:
            sentences = Sentence.objects.filter(
                document_id__in=self.documents
            ).prefetch_related('tokens')
        else:
            sentences = Sentence.objects.all().prefetch_related('tokens')
        
        ngram_counts = {}
        
        for sentence in sentences:
            tokens = list(sentence.tokens.order_by('index'))
            
            # Generate n-grams
            for i in range(len(tokens) - n + 1):
                ngram_tokens = tokens[i:i+n]
                
                # Skip if contains punctuation
                if any(t.upos == 'PUNCT' for t in ngram_tokens):
                    continue
                
                # Build n-gram string
                if use_lemma:
                    ngram_str = ' '.join(t.lemma for t in ngram_tokens)
                else:
                    ngram_str = ' '.join(t.form for t in ngram_tokens)
                
                ngram_str = ngram_str.lower()
                
                if ngram_str not in ngram_counts:
                    ngram_counts[ngram_str] = 0
                ngram_counts[ngram_str] += 1
        
        # Filter and sort
        results = [
            {'ngram': ngram, 'frequency': count}
            for ngram, count in ngram_counts.items()
            if count >= min_frequency
        ]
        results.sort(key=lambda x: x['frequency'], reverse=True)
        
        return results[:limit]
    
    def pos_distribution(self) -> Dict[str, int]:
        """Get POS tag distribution.
        
        Returns:
            Dict mapping POS tags to counts
        """
        pos_counts = self.base_queryset.values('upos').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {item['upos']: item['count'] for item in pos_counts if item['upos']}
    
    def word_frequency(
        self,
        use_lemma: bool = True,
        limit: int = 100,
        min_length: int = 1
    ) -> List[Dict]:
        """Word frequency list.
        
        Args:
            use_lemma: Use lemmas (True) or forms (False)
            limit: Max results
            min_length: Minimum word length
        
        Returns:
            List of words with frequencies
        """
        field = 'lemma' if use_lemma else 'form'

        # Base queryset excluding punctuation
        base = self.base_queryset.exclude(upos='PUNCT')

        # Total tokens to compute percentages
        try:
            total_tokens = base.count() or 1
        except Exception:
            total_tokens = 1

        # Count frequencies and also gather a representative POS tag
        freq_qs = base.values(field).annotate(
            count=Count('id')
        ).order_by('-count')[:limit]

        results = []
        for item in freq_qs:
            word = item.get(field)
            if not word or len(word) < min_length:
                continue

            frequency = item.get('count', 0)

            # Determine the most common POS for this token/lemma
            pos_q = base.filter(**{f"{field}__iexact": word}).values('upos').annotate(c=Count('id')).order_by('-c')
            pos = pos_q[0]['upos'] if pos_q and pos_q[0].get('upos') else ''

            # If using lemma, include lemma explicitly; otherwise lemma == word
            lemma = word if use_lemma else ''

            percentage = (frequency / total_tokens) * 100

            results.append({
                'word': word,
                'lemma': lemma,
                'pos': pos,
                'frequency': frequency,
                'percentage': round(percentage, 4)
            })

        return results
