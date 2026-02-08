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

        # Log raw format for debugging
        logger.debug(f"Normalizing analysis: type={type(analysis)}, len={len(analysis)}")
        if len(analysis) > 0:
            logger.debug(f"First item type: {type(analysis[0])}, value: {analysis[0]}")

        # If already normalized (dicts), return as-is
        if isinstance(analysis[0], dict):
            logger.debug("Analysis already in dict format")
            return analysis

        # If items are strings, try to group into triplets
        if all(isinstance(x, str) for x in analysis):
            logger.debug("Analysis in flat string format, grouping into triplets")
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
            logger.debug(f"Grouped into {len(tokens)} tokens")
            return tokens

        # Fallback: return empty
        logger.warning(f"Unknown analysis format: {type(analysis[0])}")
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
            logger.warning(f"No document or analysis found for doc_id={doc_id}")
            return []

        analysis = self._normalize_analysis(doc['analysis'])
        logger.info(f"Search word '{pattern}': normalized {len(analysis)} tokens")
        
        if len(analysis) > 0:
            logger.debug(f"First 3 tokens: {analysis[:3]}")
        
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
                    
        logger.info(f"Search word '{pattern}': found {len(matches)} matches")
        if len(matches) == 0 and len(analysis) > 0:
            # Debug: show sample of original and cleaned words
            sample_orig = [t.get('word', '') for t in analysis[:10]]
            sample_cleaned = [self._clean_text(t.get('word', '')) for t in analysis[:10]]
            logger.debug(f"Sample original words: {sample_orig}")
            logger.debug(f"Sample cleaned words: {sample_cleaned}")
            logger.debug(f"Pattern original: '{pattern}'")
            logger.debug(f"Pattern cleaned: '{self._clean_text(pattern)}'")
            
            # Check if 'benzer' exists in original words
            benzer_in_orig = any('benzer' in t.get('word', '').lower() for t in analysis)
            logger.debug(f"'benzer' found in original words: {benzer_in_orig}")

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

        if not doc:
            return []

        # Normalize analysis into list of token dicts
        analysis = self._normalize_analysis(doc.get('analysis', []))
        if not analysis:
            return []

        concordance = []

        # Build a quick index of token positions by (word,lemma,pos) to help
        # resolve matches that didn't include an explicit 'position'.
        index_by_tuple = {}
        for i, tok in enumerate(analysis):
            key = (tok.get('word', ''), tok.get('lemma', ''), tok.get('pos', ''))
            index_by_tuple.setdefault(key, []).append(i)

        def resolve_position(m: Dict[str, Any]) -> Optional[int]:
            # Prefer provided position
            if isinstance(m.get('position'), int):
                p = m['position']
                if 0 <= p < len(analysis):
                    return p

            # Try to match by exact tuple
            key = (m.get('word', ''), m.get('lemma', ''), m.get('pos', ''))
            if key in index_by_tuple and index_by_tuple[key]:
                return index_by_tuple[key][0]

            # Fallback: search for word substring (cleaned)
            word_search = m.get('word', '')
            if word_search:
                word_search_c = self._clean_text(word_search)
                for i, tok in enumerate(analysis):
                    if word_search_c and word_search_c in self._clean_text(tok.get('word', '')):
                        return i

            return None

        for match in matches:
            pos = resolve_position(match)
            if pos is None:
                # skip matches we cannot locate
                continue

            # Extract context window
            left_start = max(0, pos - context_words)
            right_end = min(len(analysis), pos + context_words + 1)

            left_ctx = analysis[left_start:pos]
            center = analysis[pos]
            right_ctx = analysis[pos+1:right_end]

            # Build word lists and word;pos pairs
            left_words = [t.get('word', '') for t in left_ctx]
            right_words = [t.get('word', '') for t in right_ctx]
            center_word = center.get('word', '')

            left_pairs = [f"{t.get('word','')};{t.get('pos','')}" for t in left_ctx]
            right_pairs = [f"{t.get('word','')};{t.get('pos','')}" for t in right_ctx]
            center_pair = f"{center.get('word','')};{center.get('pos','')}"

            entry = {
                # legacy keys
                'left': ' '.join(left_words),
                'center': center_word,
                'right': ' '.join(right_words),
                # template-friendly keys
                'left_context': ' '.join(left_words),
                'keyword': center_word,
                'right_context': ' '.join(right_words),
                # new pair-aware keys
                'left_pairs': left_pairs,
                'keyword_pair': center_pair,
                'right_pairs': right_pairs,
                'position': pos,
                'lemma': match.get('lemma', center.get('lemma', '')),
                'pos': match.get('pos', center.get('pos', '')),
                'confidence': match.get('confidence', center.get('confidence', 1.0)),
                'warning': match.get('warning', '')
            }

            concordance.append(entry)

        return concordance

    def get_text_based_concordance(
        self,
        doc_id: int,
        pattern: str,
        context_words: int = 5,
        regex: bool = False,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """Generate KWIC concordance directly from cleaned text.
        
        This method searches in the raw text rather than the analysis tokens,
        ensuring that all words are found regardless of POS tagging.
        
        Args:
            doc_id: Document ID
            pattern: Search pattern
            context_words: Number of words on each side
            regex: Use regex matching
            case_sensitive: Case-sensitive search
            
        Returns:
            Concordance results with left/center/right context
        """
        doc = self.db.get_document(doc_id)
        if not doc:
            logger.warning(f"No document found for doc_id={doc_id}")
            return []
            
        text = doc.get('cleaned_text', '')
        if not text:
            logger.warning(f"No cleaned text for doc_id={doc_id}")
            return []
            
        # Build analysis lookup for POS/lemma enrichment
        analysis = self._normalize_analysis(doc.get('analysis', []))
        
        # Create multiple lookup strategies for better matching
        # 1. Exact match (original)
        # 2. Cleaned match (normalized)
        # 3. Position-based match
        analysis_by_original = {}
        analysis_by_cleaned = {}
        
        for idx, t in enumerate(analysis):
            word_orig = t.get('word', '').strip()
            word_clean = self._clean_text(word_orig)
            
            # Store by original (case-insensitive)
            if word_orig:
                key_orig = word_orig.lower()
                if key_orig not in analysis_by_original:
                    analysis_by_original[key_orig] = t
            
            # Store by cleaned
            if word_clean:
                if word_clean not in analysis_by_cleaned:
                    analysis_by_cleaned[word_clean] = t
        
        logger.info(f"Built analysis lookup: {len(analysis_by_original)} original, {len(analysis_by_cleaned)} cleaned")
        logger.debug(f"Sample analysis items: {list(analysis[:3])}")
        logger.debug(f"Sample lookup keys (original): {list(analysis_by_original.keys())[:10]}")
        logger.debug(f"Sample lookup keys (cleaned): {list(analysis_by_cleaned.keys())[:10]}")
        
        # Tokenize text into words
        words = re.findall(r'\S+', text)  # Split on whitespace
        logger.info(f"Text-based search: {len(words)} words in text")
        
        concordance = []
        
        # Search through words
        for idx, word in enumerate(words):
            matched = False
            
            if regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                if re.search(pattern, word, flags):
                    matched = True
            else:
                if case_sensitive:
                    if pattern in word:
                        matched = True
                else:
                    if pattern.lower() in word.lower():
                        matched = True
            
            if matched:
                # Extract context
                left_start = max(0, idx - context_words)
                right_end = min(len(words), idx + context_words + 1)
                
                left_words = words[left_start:idx]
                keyword = words[idx]
                right_words = words[idx+1:right_end]
                
                # Try to enrich with analysis data - multiple strategies
                def get_analysis_data(w):
                    """Get POS/lemma for a word using multiple lookup strategies."""
                    w_strip = w.strip()
                    
                    # Strategy 1: Exact original match (case-insensitive)
                    data = analysis_by_original.get(w_strip.lower())
                    if data:
                        logger.debug(f"Found '{w}' via original lookup: pos={data.get('pos')}")
                        return data
                    
                    # Strategy 2: Cleaned match
                    w_clean = self._clean_text(w_strip)
                    data = analysis_by_cleaned.get(w_clean)
                    if data:
                        logger.debug(f"Found '{w}' via cleaned lookup: pos={data.get('pos')}")
                        return data
                    
                    # Strategy 3: Partial cleaned match (for punctuation differences)
                    for clean_key, analysis_item in analysis_by_cleaned.items():
                        if w_clean in clean_key or clean_key in w_clean:
                            logger.debug(f"Found '{w}' via partial match with '{clean_key}': pos={analysis_item.get('pos')}")
                            return analysis_item
                    
                    logger.debug(f"No analysis data found for word '{w}' (cleaned: '{w_clean}')")
                    return {}
                
                keyword_data = get_analysis_data(keyword)
                
                # Build pairs for context words
                left_pairs = []
                for w in left_words:
                    w_data = get_analysis_data(w)
                    pos_tag = w_data.get('pos', '')
                    left_pairs.append(f"{w};{pos_tag}")
                
                right_pairs = []
                for w in right_words:
                    w_data = get_analysis_data(w)
                    pos_tag = w_data.get('pos', '')
                    right_pairs.append(f"{w};{pos_tag}")
                
                keyword_pos = keyword_data.get('pos', '')
                keyword_lemma = keyword_data.get('lemma', '')
                
                entry = {
                    'left_context': ' '.join(left_words),
                    'keyword': keyword,
                    'right_context': ' '.join(right_words),
                    'left': ' '.join(left_words),
                    'center': keyword,
                    'right': ' '.join(right_words),
                    'position': idx,
                    'lemma': keyword_lemma,
                    'pos': keyword_pos,
                    'confidence': keyword_data.get('confidence', 1.0),
                    'left_pairs': left_pairs,
                    'keyword_pair': f"{keyword};{keyword_pos}",
                    'right_pairs': right_pairs,
                }
                
                concordance.append(entry)
        
        logger.info(f"Text-based search for '{pattern}': found {len(concordance)} matches")
        if len(concordance) > 0:
            logger.debug(f"Sample match POS: {concordance[0].get('pos')}, lemma: {concordance[0].get('lemma')}")
        
        return concordance
