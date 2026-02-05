"""Advanced search engine for corpus queries.

Provides:
- Regex pattern matching
- Lemma-based search
- Multi-filter concordance (POS, confidence, morphology)
- Context window control
"""
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CorpusSearchEngine:
    """Advanced search engine for linguistic corpus."""

    def __init__(self, db_manager):
        """Initialize search engine.

        Args:
            db_manager: DatabaseManager instance
        """
        self.db = db_manager
        # Cache for normalized analyses to avoid repeated work
        self._normalized_cache = {}

    def _normalize_analysis(self, analysis):
        """Normalize analysis into a list of token dicts.

        Supports two formats seen in the project:
        - List[dict]: each item already a dict with keys like 'word','lemma','pos'
        - Flat List[str]: repeating groups (word, lemma, pos, word, lemma, pos...)

        Returns a list of dicts with at least 'word', 'lemma', 'pos' keys.
        """
        if not analysis:
            return []

        # If already normalized (dicts), return as-is
        if isinstance(analysis[0], dict):
            return analysis

        # If items are strings, try to group into triplets
        if all(isinstance(x, str) for x in analysis):
            tokens = []
            i = 0
            n = len(analysis)
            # Attempt grouping by 3 (word, lemma, pos)
            while i < n:
                word = analysis[i] if i < n else ''
                lemma = analysis[i+1] if i+1 < n else ''
                pos = analysis[i+2] if i+2 < n else ''
                tokens.append({'word': word, 'lemma': lemma, 'pos': pos, 'confidence': 1.0})
                i += 3
            return tokens

        # Fallback: return empty
        return []

    def _clean_text(self, s: str) -> str:
        """Normalize unicode, strip punctuation and casefold for robust matching."""
        if s is None:
            return ''
        # Normalize unicode (NFC), remove punctuation, and casefold
        s_norm = unicodedata.normalize('NFC', s)
        # remove punctuation (keep letters, numbers, underscore and whitespace)
        s_clean = re.sub(r"[^\w\s]", "", s_norm, flags=re.UNICODE)
        return s_clean.casefold().strip()

    def search_word(
        self,
        pattern: str,
        doc_id: Optional[int] = None,
        regex: bool = False,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for words matching pattern.

        Args:
            pattern: Search pattern
            doc_id: Document ID (None = all docs)
            regex: Use regex matching
            case_sensitive: Case-sensitive search

        Returns:
            List of matching analysis items with positions
        """
        doc = self.db.get_document(doc_id) if doc_id else None

        if not doc or not doc.get('analysis'):
            return []

        analysis = self._normalize_analysis(doc['analysis'])
        matches = []

        for idx, item in enumerate(analysis):
            if not isinstance(item, dict):
                continue

            word = item.get('word', '')

            # Apply pattern matching
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                if re.search(pattern, word, flags):
                    matches.append({**item, 'position': idx})
            else:
                if case_sensitive:
                    word_cmp = word
                    pattern_cmp = pattern
                else:
                    word_cmp = self._clean_text(word)
                    pattern_cmp = self._clean_text(pattern)

                # substring match on cleaned forms
                if pattern_cmp and pattern_cmp in word_cmp:
                    matches.append({**item, 'position': idx})

        return matches

    def search_lemma(
        self,
        lemma: str,
        doc_id: Optional[int] = None,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """Search by lemma (root form).

        Args:
            lemma: Lemma to search for
            doc_id: Document ID
            case_sensitive: Case-sensitive search

        Returns:
            Matching items
        """
        doc = self.db.get_document(doc_id) if doc_id else None

        if not doc or not doc.get('analysis'):
            return []

        analysis = self._normalize_analysis(doc['analysis'])
        matches = []

        lemma_cmp = lemma if case_sensitive else lemma.lower()

        for idx, item in enumerate(analysis):
            if not isinstance(item, dict):
                continue

            item_lemma = item.get('lemma', '')
            item_lemma_cmp = item_lemma if case_sensitive else item_lemma.lower()

            if item_lemma_cmp == lemma_cmp:
                matches.append({**item, 'position': idx})

        return matches

    def search_pos(
        self,
        pos_tags: List[str],
        doc_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search by POS tag(s).

        Args:
            pos_tags: List of POS tags to match
            doc_id: Document ID

        Returns:
            Matching items
        """
        doc = self.db.get_document(doc_id) if doc_id else None

        if not doc or not doc.get('analysis'):
            return []

        analysis = self._normalize_analysis(doc['analysis'])
        matches = []

        for idx, item in enumerate(analysis):
            if not isinstance(item, dict):
                continue

            pos = item.get('pos', '')
            if pos in pos_tags:
                matches.append({**item, 'position': idx})

        return matches

    def complex_query(
        self,
        doc_id: int,
        word_pattern: Optional[str] = None,
        lemma: Optional[str] = None,
        pos_tags: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        regex: bool = False,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """Execute complex multi-filter query.

        Args:
            doc_id: Document ID
            word_pattern: Word pattern to search
            lemma: Lemma to search
            pos_tags: POS tags to filter
            min_confidence: Minimum confidence
            max_confidence: Maximum confidence
            regex: Use regex for word pattern
            case_sensitive: Case-sensitive search

        Returns:
            Filtered matches
        """
        doc = self.db.get_document(doc_id)

        if not doc or not doc.get('analysis'):
            return []

        analysis = self._normalize_analysis(doc['analysis'])
        matches = []

        for idx, item in enumerate(analysis):
            if not isinstance(item, dict):
                continue

            # Apply all filters
            passed = True

            # Word pattern filter
            if word_pattern:
                word = item.get('word', '')
                if regex:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    if not re.search(word_pattern, word, flags):
                        passed = False
                else:
                    if case_sensitive:
                        word_cmp = word
                        pattern_cmp = word_pattern
                    else:
                        word_cmp = self._clean_text(word)
                        pattern_cmp = self._clean_text(word_pattern)

                    if not pattern_cmp or pattern_cmp not in word_cmp:
                        passed = False

            # Lemma filter
            if passed and lemma:
                item_lemma = item.get('lemma', '')
                lemma_cmp = lemma if case_sensitive else lemma.lower()
                item_lemma_cmp = item_lemma if case_sensitive else item_lemma.lower()
                if item_lemma_cmp != lemma_cmp:
                    passed = False

            # POS filter
            if passed and pos_tags:
                pos = item.get('pos', '')
                if pos not in pos_tags:
                    passed = False

            # Confidence filter
            if passed:
                conf = item.get('confidence', 1.0)
                if not (min_confidence <= conf <= max_confidence):
                    passed = False

            if passed:
                matches.append({**item, 'position': idx})

        return matches

    def get_concordance(
        self,
        matches: List[Dict[str, Any]],
        doc_id: int,
        context_words: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate KWIC concordance from matches.

        Args:
            matches: Search results with positions
            doc_id: Document ID
            context_words: Number of words on each side

        Returns:
            Concordance results with left/center/right context
        """
        doc = self.db.get_document(doc_id)
        
        if not doc or not doc.get('analysis'):
            return []

        analysis = self._normalize_analysis(doc.get('analysis', []))
        concordance = []

        for match in matches:
            pos = match.get('position', 0)
            
            # Extract context
            left_start = max(0, pos - context_words)
            right_end = min(len(analysis), pos + context_words + 1)

            left_ctx = analysis[left_start:pos]
            center = analysis[pos:pos+1]
            right_ctx = analysis[pos+1:right_end]

            # Extract words (analysis items are normalized dicts)
            left_words = [item.get('word', '') for item in left_ctx]
            center_word = center[0].get('word', '') if center else ''
            right_words = [item.get('word', '') for item in right_ctx]

            entry = {
                # backward-compatible keys
                'left': ' '.join(left_words),
                'center': center_word,
                'right': ' '.join(right_words),
                # template-friendly keys
                'left_context': ' '.join(left_words),
                'keyword': center_word,
                'right_context': ' '.join(right_words),
                'position': pos,
                'lemma': match.get('lemma', ''),
                'pos': match.get('pos', ''),
                'confidence': match.get('confidence', 1.0),
                'warning': match.get('warning', '')
            }
            concordance.append(entry)

        return concordance
