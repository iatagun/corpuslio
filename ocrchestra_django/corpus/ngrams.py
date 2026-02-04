"""N-gram and collocation analysis module."""

from collections import Counter, defaultdict
import math


class NgramAnalyzer:
    """Extract and analyze n-grams and collocations."""
    
    def __init__(self, analysis_data):
        """
        Initialize with analysis data.
        
        Args:
            analysis_data: List of dicts with 'word', 'lemma', 'pos' keys
        """
        self.data = analysis_data
        self.words = [item.get('word', '').lower() for item in analysis_data if isinstance(item, dict)]
        self.total_words = len(self.words)
    
    def extract_ngrams(self, n=2):
        """
        Extract n-grams from text.
        
        Args:
            n: N-gram size (2=bigram, 3=trigram)
        
        Returns:
            Counter object with n-grams and frequencies
        """
        ngrams = []
        for i in range(len(self.words) - n + 1):
            ngram = tuple(self.words[i:i+n])
            ngrams.append(ngram)
        
        return Counter(ngrams)
    
    def get_top_ngrams(self, n=2, top_k=50):
        """
        Get top k n-grams.
        
        Args:
            n: N-gram size
            top_k: Number of top n-grams to return
        
        Returns:
            List of tuples: (ngram, count)
        """
        ngrams = self.extract_ngrams(n)
        return ngrams.most_common(top_k)
    
    def calculate_collocation_scores(self, word1, word2, window=5):
        """
        Calculate collocation scores for word pair.
        
        Args:
            word1: First word
            word2: Second word  
            window: Context window size
        
        Returns:
            Dict with MI, T-score, and frequency
        """
        word1 = word1.lower()
        word2 = word2.lower()
        
        # Count occurrences
        c1 = self.words.count(word1)
        c2 = self.words.count(word2)
        c12 = 0  # Co-occurrence count
        
        # Find co-occurrences within window
        for i, w in enumerate(self.words):
            if w == word1:
                context = self.words[max(0, i-window):min(len(self.words), i+window+1)]
                c12 += context.count(word2)
        
        if c12 == 0:
            return None
        
        # Calculate probabilities
        p1 = c1 / self.total_words
        p2 = c2 / self.total_words
        p12 = c12 / self.total_words
        
        # Mutual Information (MI)
        try:
            mi = math.log2(p12 / (p1 * p2))
        except (ValueError, ZeroDivisionError):
            mi = 0
        
        # T-score
        try:
            t_score = (p12 - p1 * p2) / math.sqrt(p12 / self.total_words)
        except (ValueError, ZeroDivisionError):
            t_score = 0
        
        return {
            'frequency': c12,
            'mutual_information': mi,
            't_score': t_score,
            'word1_freq': c1,
            'word2_freq': c2
        }
    
    def find_collocations(self, target_word, top_k=20, window=5, min_freq=2):
        """
        Find top collocates for a target word.
        
        Args:
            target_word: Word to find collocates for
            top_k: Number of top collocates
            window: Context window
            min_freq: Minimum co-occurrence frequency
        
        Returns:
            List of dicts with collocate info, sorted by MI score
        """
        target_word = target_word.lower()
        collocates = defaultdict(int)
        
        # Find all words co-occurring with target
        for i, w in enumerate(self.words):
            if w == target_word:
                context_start = max(0, i - window)
                context_end = min(len(self.words), i + window + 1)
                context = self.words[context_start:i] + self.words[i+1:context_end]
                
                for collocate in context:
                    if collocate != target_word:
                        collocates[collocate] += 1
        
        # Calculate scores for each collocate
        results = []
        for collocate, freq in collocates.items():
            if freq >= min_freq:
                scores = self.calculate_collocation_scores(target_word, collocate, window)
                if scores:
                    results.append({
                        'collocate': collocate,
                        **scores
                    })
        
        # Sort by MI score
        results.sort(key=lambda x: x['mutual_information'], reverse=True)
        return results[:top_k]
    
    def get_ngram_pos_patterns(self, n=2, top_k=30):
        """
        Extract POS n-gram patterns.
        
        Args:
            n: N-gram size
            top_k: Number of top patterns
        
        Returns:
            List of tuples: (pos_pattern, count)
        """
        pos_tags = [item.get('pos', 'UNK') for item in self.data if isinstance(item, dict)]
        
        ngrams = []
        for i in range(len(pos_tags) - n + 1):
            ngram = tuple(pos_tags[i:i+n])
            ngrams.append(ngram)
        
        return Counter(ngrams).most_common(top_k)
