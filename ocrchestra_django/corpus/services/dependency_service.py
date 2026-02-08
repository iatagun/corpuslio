"""
Dependency Service for CoNLL-U dependency queries.

Provides methods for querying dependency structures:
- Find tokens by dependency relation (nsubj, obj, etc.)
- Find head-dependent pairs
- Pattern matching
- Tree extraction
"""

from typing import List, Dict, Optional, Tuple
from corpus.models import Document, Analysis


class DependencyService:
    """Service for dependency-based queries on analyzed documents."""
    
    def __init__(self, document: Optional[Document] = None):
        """
        Initialize dependency service.
        
        Args:
            document: Optional document to query. If None, must pass document_id to methods.
        """
        self.document = document
    
    def _get_tokens(self, document_id: Optional[int] = None) -> List[Dict]:
        """
        Get CoNLL-U tokens for a document.
        
        Args:
            document_id: Document ID (overrides self.document if provided)
            
        Returns:
            List of token dictionaries
            
        Raises:
            ValueError: If document has no dependency data
        """
        if document_id:
            document = Document.objects.select_related('analysis').get(id=document_id)
        elif self.document:
            document = self.document
        else:
            raise ValueError("No document specified")
        
        if not hasattr(document, 'analysis') or not document.analysis.has_dependencies:
            raise ValueError(f"Document {document.filename} has no dependency annotations")
        
        return document.analysis.conllu_data or []
    
    def find_by_deprel(
        self,
        deprel: str,
        document_id: Optional[int] = None,
        upos: Optional[str] = None
    ) -> List[Dict]:
        """
        Find all tokens with specific dependency relation.
        
        Args:
            deprel: Dependency relation (e.g., 'nsubj', 'obj', 'obl')
            document_id: Optional document ID
            upos: Optional POS tag filter
            
        Returns:
            List of matching tokens with context
            
        Example:
            >>> service = DependencyService()
            >>> subjects = service.find_by_deprel('nsubj', document_id=10)
            >>> for subj in subjects:
            ...     print(f"{subj['form']} is subject of {subj['head_form']}")
        """
        tokens = self._get_tokens(document_id)
        results = []
        
        # Create lookup dict for fast access
        token_by_id = {t['id']: t for t in tokens if t.get('sentence_id') is not None}
        
        for token in tokens:
            # Match dependency relation
            if token.get('deprel') != deprel:
                continue
            
            # Match POS tag if specified
            if upos and token.get('upos') != upos:
                continue
            
            # Get head token
            head_id = token.get('head', 0)
            head_token = token_by_id.get(head_id) if head_id != 0 else None
            
            result = {
                'token_id': token['id'],
                'form': token['form'],
                'lemma': token['lemma'],
                'upos': token['upos'],
                'feats': token.get('feats', {}),
                'deprel': token['deprel'],
                'head_id': head_id,
                'head_form': head_token['form'] if head_token else 'ROOT',
                'head_lemma': head_token['lemma'] if head_token else 'ROOT',
                'head_upos': head_token['upos'] if head_token else 'ROOT',
                'sentence_id': token.get('sentence_id', 0),
                'sentence_text': token.get('sentence_text', '')
            }
            
            results.append(result)
        
        return results
    
    def find_head_dependent_pairs(
        self,
        document_id: Optional[int] = None,
        head_lemma: Optional[str] = None,
        head_pos: Optional[str] = None,
        deprel: Optional[str] = None,
        dependent_pos: Optional[str] = None
    ) -> List[Dict]:
        """
        Find head-dependent pairs matching criteria.
        
        Args:
            document_id: Optional document ID
            head_lemma: Lemma of the head (e.g., 'yazmak')
            head_pos: POS tag of the head (e.g., 'VERB')
            deprel: Dependency relation (e.g., 'obj')
            dependent_pos: POS tag of the dependent (e.g., 'NOUN')
            
        Returns:
            List of head-dependent pairs
            
        Example:
            >>> # Find all objects of verb 'yazmak'
            >>> pairs = service.find_head_dependent_pairs(
            ...     document_id=10,
            ...     head_lemma='yazmak',
            ...     deprel='obj'
            ... )
        """
        tokens = self._get_tokens(document_id)
        results = []
        
        # Create lookup dict
        token_by_id = {t['id']: t for t in tokens if t.get('sentence_id') is not None}
        
        for token in tokens:
            head_id = token.get('head', 0)
            if head_id == 0:
                continue
            
            head_token = token_by_id.get(head_id)
            if not head_token:
                continue
            
            # Apply filters
            if head_lemma and head_token.get('lemma') != head_lemma:
                continue
            
            if head_pos and head_token.get('upos') != head_pos:
                continue
            
            if deprel and token.get('deprel') != deprel:
                continue
            
            if dependent_pos and token.get('upos') != dependent_pos:
                continue
            
            result = {
                'head_id': head_id,
                'head_form': head_token['form'],
                'head_lemma': head_token['lemma'],
                'head_upos': head_token['upos'],
                'dependent_id': token['id'],
                'dependent_form': token['form'],
                'dependent_lemma': token['lemma'],
                'dependent_upos': token['upos'],
                'deprel': token['deprel'],
                'sentence_id': token.get('sentence_id', 0),
                'sentence_text': token.get('sentence_text', '')
            }
            
            results.append(result)
        
        return results
    
    def find_by_pattern(
        self,
        pattern: str,
        document_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Find dependency patterns using simplified syntax.
        
        Pattern syntax:
            "NOUN:nsubj>VERB" - NOUN is subject of VERB
            "VERB:obj>NOUN" - VERB has object NOUN
            "ADJ:amod>NOUN" - ADJ modifies NOUN
        
        Args:
            pattern: Pattern string (POS:deprel>POS format)
            document_id: Optional document ID
            
        Returns:
            List of matching patterns
            
        Example:
            >>> # Find all NOUN subjects of VERBs
            >>> matches = service.find_by_pattern("NOUN:nsubj>VERB", document_id=10)
        """
        # Parse pattern
        import re
        match = re.match(r'([A-Z]+):(\w+)>([A-Z]+)', pattern)
        if not match:
            raise ValueError(f"Invalid pattern: {pattern}. Use format 'POS:deprel>POS'")
        
        dependent_pos, deprel, head_pos = match.groups()
        
        # Use find_head_dependent_pairs with filters
        return self.find_head_dependent_pairs(
            document_id=document_id,
            head_pos=head_pos,
            deprel=deprel,
            dependent_pos=dependent_pos
        )
    
    def get_sentence_tree(
        self,
        sentence_id: int,
        document_id: Optional[int] = None
    ) -> Dict:
        """
        Get full dependency tree for a sentence.
        
        Args:
            sentence_id: Sentence index (0-based)
            document_id: Optional document ID
            
        Returns:
            Tree structure with root and children
            
        Example:
            >>> tree = service.get_sentence_tree(0, document_id=10)
            >>> print(tree['root']['form'])
            >>> for child in tree['children']:
            ...     print(child['form'], child['deprel'])
        """
        tokens = self._get_tokens(document_id)
        
        # Get tokens for this sentence
        sentence_tokens = [t for t in tokens if t.get('sentence_id') == sentence_id]
        
        if not sentence_tokens:
            raise ValueError(f"No tokens found for sentence {sentence_id}")
        
        # Build tree using ocrchestra.parsers.conllu_parser utility
        from ocrchestra.parsers.conllu_parser import build_tree, find_root
        
        root = find_root(sentence_tokens)
        if not root:
            raise ValueError(f"No root found for sentence {sentence_id}")
        
        # Build full tree structure
        tree_structure = build_tree(sentence_tokens)
        
        # Add sentence metadata
        sentence_text = sentence_tokens[0].get('sentence_text', '') if sentence_tokens else ''
        
        return {
            'sentence_id': sentence_id,
            'sentence_text': sentence_text,
            'token_count': len(sentence_tokens),
            'tree': tree_structure
        }
    
    def get_sentence_count(self, document_id: Optional[int] = None) -> int:
        """
        Get number of sentences in document.
        
        Args:
            document_id: Optional document ID
            
        Returns:
            Number of sentences
        """
        tokens = self._get_tokens(document_id)
        if not tokens:
            return 0
        
        sentence_ids = set(t.get('sentence_id', 0) for t in tokens)
        return len(sentence_ids)
    
    def get_deprel_distribution(self, document_id: Optional[int] = None) -> Dict[str, int]:
        """
        Get distribution of dependency relations in document.
        
        Args:
            document_id: Optional document ID
            
        Returns:
            Dictionary mapping deprel to count
        """
        tokens = self._get_tokens(document_id)
        
        from collections import Counter
        deprels = [t.get('deprel', 'UNKNOWN') for t in tokens]
        return dict(Counter(deprels))
    
    def search_by_features(
        self,
        features: Dict[str, str],
        document_id: Optional[int] = None,
        upos: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for tokens with specific morphological features.
        
        Args:
            features: Dictionary of feature-value pairs (e.g., {'Case': 'Acc', 'Number': 'Sing'})
            document_id: Optional document ID
            upos: Optional POS tag filter
            
        Returns:
            List of matching tokens
            
        Example:
            >>> # Find all accusative case nouns
            >>> tokens = service.search_by_features(
            ...     {'Case': 'Acc'},
            ...     document_id=10,
            ...     upos='NOUN'
            ... )
        """
        tokens = self._get_tokens(document_id)
        results = []
        
        for token in tokens:
            # Match POS tag if specified
            if upos and token.get('upos') != upos:
                continue
            
            # Match features
            token_feats = token.get('feats', {})
            if not all(token_feats.get(k) == v for k, v in features.items()):
                continue
            
            results.append({
                'token_id': token['id'],
                'form': token['form'],
                'lemma': token['lemma'],
                'upos': token['upos'],
                'feats': token_feats,
                'deprel': token.get('deprel', ''),
                'sentence_id': token.get('sentence_id', 0),
                'sentence_text': token.get('sentence_text', '')
            })
        
        return results
    
    def get_statistics(self, document_id: Optional[int] = None) -> Dict:
        """
        Get overall dependency statistics for document.
        
        Args:
            document_id: Optional document ID
            
        Returns:
            Statistics dictionary
        """
        tokens = self._get_tokens(document_id)
        
        from collections import Counter
        
        # Count sentences
        sentence_count = len(set(t.get('sentence_id', 0) for t in tokens))
        
        # Count tokens
        token_count = len(tokens)
        
        # Average sentence length
        avg_sent_length = token_count / sentence_count if sentence_count > 0 else 0
        
        # POS distribution
        pos_dist = Counter(t.get('upos', 'UNKNOWN') for t in tokens)
        
        # Deprel distribution
        deprel_dist = Counter(t.get('deprel', 'UNKNOWN') for t in tokens)
        
        # Average dependency distance
        dep_distances = []
        for token in tokens:
            head = token.get('head', 0)
            if head != 0:
                distance = abs(token['id'] - head)
                dep_distances.append(distance)
        
        avg_dep_distance = sum(dep_distances) / len(dep_distances) if dep_distances else 0
        
        return {
            'sentence_count': sentence_count,
            'token_count': token_count,
            'avg_sentence_length': round(avg_sent_length, 2),
            'pos_distribution': dict(pos_dist.most_common(10)),
            'deprel_distribution': dict(deprel_dist.most_common(10)),
            'avg_dependency_distance': round(avg_dep_distance, 2)
        }
