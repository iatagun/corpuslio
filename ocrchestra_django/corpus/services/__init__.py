"""
Corpus services package.
"""

from .export_service import ExportService

# Import CorpusService directly (legacy module handles import errors internally)
try:
    from .legacy import CorpusService
except ImportError as e:
    import warnings
    warnings.warn(f"CorpusService could not be imported: {e}")
    
    # Create a functional fallback CorpusService with basic methods
    from collections import Counter
    from corpus.models import Token
    
    class CorpusService:
        """Fallback CorpusService when legacy module cannot be imported."""
        
        def __init__(self):
            pass
        
        def get_statistics(self, document):
            """Get statistics from Token model (new corpus platform)."""
            if Token.objects.filter(document=document).exists():
                tokens = Token.objects.filter(document=document).select_related('sentence')
                
                forms = [t.form for t in tokens if t.form and t.upos != 'PUNCT']
                lemmas = [t.lemma for t in tokens if t.lemma and t.upos != 'PUNCT']
                pos_tags = [t.upos for t in tokens if t.upos]
                
                token_count = len(forms)
                type_count = len(set(forms))
                ttr = type_count / token_count if token_count > 0 else 0.0
                
                word_freq = Counter(forms).most_common(50)
                lemma_freq = Counter(lemmas).most_common(50)
                pos_dist = Counter(pos_tags)
                
                return {
                    'token_count': token_count,
                    'type_count': type_count,
                    'ttr': round(ttr, 4),
                    'word_frequency': [{'word': w, 'count': c} for w, c in word_freq],
                    'lemma_frequency': [{'lemma': l, 'count': c} for l, c in lemma_freq],
                    'pos_distribution': [{'pos': p, 'count': c} for p, c in pos_dist.items()],
                    'zipf': []
                }
            return None
        
        def search_in_document(self, document, search_params):
            """Basic search not available in fallback mode."""
            return []
        
        def calculate_readability_scores(self, text):
            """Basic readability calculation."""
            if not text:
                return None
            
            import re
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            sentence_count = len(sentences) or 1
            
            words = text.split()
            word_count = len(words) or 1
            
            vowels = "aeıioöuüAEIİOÖUÜ"
            syllable_count = sum(1 for char in text if char in vowels) or 1
            
            avg_word_len_syllable = syllable_count / word_count
            avg_sentence_len_word = word_count / sentence_count
            
            atesman_score = 198.825 - (40.175 * avg_word_len_syllable) - (2.610 * avg_sentence_len_word)
            atesman_score = max(0, min(100, atesman_score))
            
            return {
                'metrics': {
                    'syllable_count': syllable_count,
                    'word_count': word_count,
                    'sentence_count': sentence_count,
                    'avg_word_len_syllable': round(avg_word_len_syllable, 2),
                    'avg_sentence_len_word': round(avg_sentence_len_word, 2)
                },
                'scores': {
                    'atesman': {
                        'score': round(atesman_score, 2),
                        'level': 'N/A'
                    }
                }
            }

__all__ = ['ExportService', 'CorpusService']
