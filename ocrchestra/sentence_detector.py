"""Sentence boundary detection for Turkish text.

Provides simple but effective sentence segmentation for corpus annotation.
"""
import re
from typing import List, Tuple


class SentenceBoundaryDetector:
    """Detect sentence boundaries in Turkish text."""
    
    def __init__(self):
        """Initialize detector with Turkish-specific rules."""
        # Common Turkish abbreviations that don't end sentences
        self.abbreviations = {
            'Dr', 'Prof', 'Doç', 'Yrd', 'Öğr', 'Arş', 'Gör',  # Academic
            'Sayın', 'Sn', 'Bay', 'Bayan', 'Bn',  # Titles
            'Ltd', 'Şti', 'A.Ş', 'Tic', 'San',  # Business
            'vb', 'vs', 'örn', 'bkz', 'krş',  # Common
            'No', 'Sok', 'Cad', 'Apt', 'Kat',  # Address
            'Tel', 'Fax', 'E-posta', 'S'  # Contact
        }
        
        # Build abbreviation pattern
        abbrev_pattern = '|'.join(re.escape(abbr) for abbr in self.abbreviations)
        
        # Sentence ending punctuation
        self.sent_end_pattern = re.compile(
            r'(?<!' + abbrev_pattern + r')'  # Not after abbreviation
            r'([.!?]+)'  # Sentence-ending punctuation
            r'(?=\s+[A-ZÇĞIÖŞÜ]|$)'  # Followed by capital or end
        )
    
    def detect_boundaries(self, text: str) -> List[Tuple[int, int]]:
        """Detect sentence boundaries in text.
        
        Args:
            text: Input text
        
        Returns:
            List of (start, end) positions for each sentence
        """
        if not text:
            return []
        
        sentences = []
        current_start = 0
        
        # Find all sentence-ending punctuation
        for match in self.sent_end_pattern.finditer(text):
            end_pos = match.end()
            
            # Skip if sentence is too short (likely false positive)
            if end_pos - current_start < 5:
                continue
            
            sentences.append((current_start, end_pos))
            current_start = end_pos
        
        # Add remaining text as final sentence if significant
        if current_start < len(text) and len(text) - current_start > 5:
            sentences.append((current_start, len(text)))
        
        return sentences
    
    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences.
        
        Args:
            text: Input text
        
        Returns:
            List of sentences
        """
        boundaries = self.detect_boundaries(text)
        return [text[start:end].strip() for start, end in boundaries]
    
    def annotate_tokens(self, tokens: List[dict], text: str) -> List[dict]:
        """Add sentence IDs to token annotations.
        
        Args:
            tokens: List of token dictionaries
            text: Original text
        
        Returns:
            Tokens with 'sent_id' field added
        """
        sentences = self.detect_boundaries(text)
        
        # Build position map
        sent_map = {}
        for sent_id, (start, end) in enumerate(sentences, 1):
            for pos in range(start, end):
                sent_map[pos] = sent_id
        
        # Assign sentence IDs to tokens
        current_pos = 0
        for token in tokens:
            if not isinstance(token, dict):
                continue
            
            word = token.get('word', '')
            
            # Find word in text (approximate)
            word_start = text.find(word, current_pos)
            if word_start >= 0:
                token['sent_id'] = sent_map.get(word_start, 1)
                current_pos = word_start + len(word)
            else:
                # Fallback: use previous sentence ID or 1
                if tokens.index(token) > 0:
                    token['sent_id'] = tokens[tokens.index(token) - 1].get('sent_id', 1)
                else:
                    token['sent_id'] = 1
        
        return tokens


def detect_paragraphs(text: str) -> List[Tuple[int, int]]:
    """Detect paragraph boundaries (simple: double newline).
    
    Args:
        text: Input text
    
    Returns:
        List of (start, end) positions for each paragraph
    """
    paragraphs = []
    
    # Split by double newlines
    parts = re.split(r'\n\s*\n', text)
    
    current_pos = 0
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Find paragraph in original text
        start = text.find(part, current_pos)
        if start >= 0:
            end = start + len(part)
            paragraphs.append((start, end))
            current_pos = end
    
    # If no paragraphs found, treat entire text as one paragraph
    if not paragraphs:
        paragraphs.append((0, len(text)))
    
    return paragraphs
