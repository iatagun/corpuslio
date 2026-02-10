"""Statistical analysis for corpus data.

Provides:
- Frequency analysis (word, lemma, POS)
- Type-token ratio
- N-gram extraction and collocation scoring
- Zipf distribution
"""
import math
from typing import List, Dict, Any, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class CorpusStatistics:
    """Statistical analysis for corpus."""

    def __init__(self, analysis_data: List[Dict[str, Any]]):
        """Initialize with analysis data.

        Args:
            analysis_data: List of annotated tokens
        """
        self.data = [item for item in analysis_data if isinstance(item, dict)]
        self.words = [item.get('word', '') for item in self.data]
        self.lemmas = [item.get('lemma', '') for item in self.data]
        self.pos_tags = [item.get('pos', '') for item in self.data]

    def token_count(self) -> int:
        """Total number of tokens."""
        return len(self.data)

    def type_count(self) -> int:
        """Number of unique words (types)."""
        return len(set(self.words))

    def type_token_ratio(self) -> float:
        """Type-Token Ratio (lexical diversity)."""
        tokens = self.token_count()
        types = self.type_count()
        return types / tokens if tokens > 0 else 0.0

    def word_frequency(self, top_n: int = 50) -> List[Tuple[str, int]]:
        """Get word frequency list.

        Args:
            top_n: Number of top items to return

        Returns:
            List of (word, count) tuples sorted by frequency
        """
        counter = Counter(self.words)
        return counter.most_common(top_n)

    def lemma_frequency(self, top_n: int = 50) -> List[Tuple[str, int]]:
        """Get lemma frequency list.

        Args:
            top_n: Number of top items

        Returns:
            List of (lemma, count) tuples
        """
        counter = Counter(self.lemmas)
        return counter.most_common(top_n)

    def pos_distribution(self) -> Dict[str, int]:
        """Get POS tag distribution.

        Returns:
            Dictionary of POS tag counts
        """
        return dict(Counter(self.pos_tags))

    def zipf_distribution(self) -> List[Tuple[int, str, int, float]]:
        """Calculate Zipf distribution.

        Returns:
            List of (rank, word, frequency, expected_freq) tuples
        """
        freq_list = self.word_frequency(top_n=100)
        total = sum(count for _, count in freq_list)
        
        zipf_data = []
        for rank, (word, count) in enumerate(freq_list, 1):
            # Zipf's law: frequency ∝ 1/rank
            expected = total / rank if rank > 0 else 0
            zipf_data.append((rank, word, count, expected))
        
        return zipf_data

    def confidence_distribution(self, bins: int = 10) -> Dict[str, int]:
        """Get confidence score distribution.

        Args:
            bins: Number of bins

        Returns:
            Dictionary of bin ranges to counts
        """
        confidences = [item.get('confidence', 1.0) for item in self.data]
        
        # Create bins
        bin_counts = {}
        bin_size = 1.0 / bins
        
        for i in range(bins):
            bin_start = i * bin_size
            bin_end = (i + 1) * bin_size
            bin_label = f"{bin_start:.1f}-{bin_end:.1f}"
            
            count = sum(1 for c in confidences if bin_start <= c < bin_end)
            bin_counts[bin_label] = count
        
        return bin_counts

    def extract_ngrams(self, n: int = 2, min_freq: int = 2) -> List[Tuple[Tuple[str, ...], int]]:
        """Extract n-grams.

        Args:
            n: N-gram size (2=bigram, 3=trigram)
            min_freq: Minimum frequency threshold

        Returns:
            List of (ngram_tuple, count) sorted by frequency
        """
        ngrams = []
        for i in range(len(self.words) - n + 1):
            ngram = tuple(self.words[i:i+n])
            ngrams.append(ngram)
        
        counter = Counter(ngrams)
        # Filter by minimum frequency
        return [(ng, count) for ng, count in counter.most_common() if count >= min_freq]

    def calculate_pmi(self, bigrams: List[Tuple[Tuple[str, str], int]]) -> List[Tuple[Tuple[str, str], float]]:
        """Calculate Pointwise Mutual Information for bigrams.

        Args:
            bigrams: List of bigram tuples and counts

        Returns:
            List of (bigram, PMI_score)
        """
        total_bigrams = sum(count for _, count in bigrams)
        word_freq = Counter(self.words)
        total_words = len(self.words)
        
        pmi_scores = []
        for (w1, w2), count in bigrams:
            # P(w1, w2)
            p_bigram = count / total_bigrams
            # P(w1) * P(w2)
            p_w1 = word_freq[w1] / total_words
            p_w2 = word_freq[w2] / total_words
            p_independent = p_w1 * p_w2
            
            # PMI = log2(P(w1,w2) / (P(w1)*P(w2)))
            if p_independent > 0:
                pmi = math.log2(p_bigram / p_independent)
                pmi_scores.append(((w1, w2), pmi))
        
        # Sort by PMI score
        pmi_scores.sort(key=lambda x: x[1], reverse=True)
        return pmi_scores

    def calculate_tscore(self, bigrams: List[Tuple[Tuple[str, str], int]]) -> List[Tuple[Tuple[str, str], float]]:
        """Calculate t-score for bigrams.

        Args:
            bigrams: List of bigram tuples and counts

        Returns:
            List of (bigram, t_score)
        """
        total_bigrams = sum(count for _, count in bigrams)
        word_freq = Counter(self.words)
        total_words = len(self.words)
        
        t_scores = []
        for (w1, w2), count in bigrams:
            # Observed frequency
            obs = count
            # Expected frequency under independence
            p_w1 = word_freq[w1] / total_words
            p_w2 = word_freq[w2] / total_words
            exp = total_bigrams * p_w1 * p_w2
            
            # t-score = (observed - expected) / sqrt(observed)
            if obs > 0:
                t = (obs - exp) / math.sqrt(obs)
                t_scores.append(((w1, w2), t))
        
        # Sort by t-score
        t_scores.sort(key=lambda x: x[1], reverse=True)
        return t_scores
