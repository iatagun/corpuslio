"""Service layer for corpus business logic."""

import sys
import os
from django.conf import settings

# Add parent ocrchestra module to path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from ocrchestra.search_engine import CorpusSearchEngine
from ocrchestra.statistics import CorpusStatistics
from ocrchestra.exporters import CorpusExporter

from .models import Document, Content, Analysis


class CorpusService:
    """Service class for corpus operations."""
    
    def __init__(self):
        """Initialize service."""
        pass
    
    def calculate_readability_scores(self, text):
        """
        Calculate readability scores for Turkish text.
        formules: Ateşman, Çetinkaya-Uzun
        """
        if not text:
            return None

        # Basic Stats
        import re
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences) or 1
        
        words = text.split()
        word_count = len(words) or 1
        
        # Syllable Calculation (Turkish vowel count)
        vowels = "aeıioöuüAEIİOÖUÜ"
        syllable_count = sum(1 for char in text if char in vowels) or 1
        
        # Averages
        avg_word_len_syllable = syllable_count / word_count
        avg_sentence_len_word = word_count / sentence_count
        
        # 1. Ateşman Readability Formula
        # Skor = 198.825 - 40.175 * (Hece/Kelime) - 2.610 * (Kelime/Cümle)
        atesman_score = 198.825 - (40.175 * avg_word_len_syllable) - (2.610 * avg_sentence_len_word)
        atesman_score = max(0, min(100, atesman_score))  # Clamp 0-100
        
        # Ateşman Interpretation
        if atesman_score >= 90: atesman_level = "Çok Kolay (4. Sınıf ve altı)"
        elif atesman_score >= 80: atesman_level = "Kolay (5-6. Sınıf)"
        elif atesman_score >= 70: atesman_level = "Orta Güçlükte (7-8. Sınıf)"
        elif atesman_score >= 60: atesman_level = "Zor (Lise)"
        elif atesman_score >= 50: atesman_level = "Çok Zor (Üniversite)"
        else: atesman_level = "Akademik/Bilimsel"

        # 2. Çetinkaya-Uzun Formula
        # Skor = 118.823 - 25.96 * (Hece/Kelime) - 0.971 * (Kelime/Cümle)
        cetinkaya_score = 118.823 - (25.96 * avg_word_len_syllable) - (0.971 * avg_sentence_len_word)
        cetinkaya_score = max(0, min(100, cetinkaya_score))
        
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
                    'level': atesman_level
                },
                'cetinkaya': {
                    'score': round(cetinkaya_score, 2)
                }
            }
        }
    
    def search_in_document(self, document, search_params):
        """
        Search within a document using CorpusSearchEngine.
        
        Args:
            document: Document model instance
            search_params: Dictionary with search parameters
        
        Returns:
            List of concordance results
        """
        if not hasattr(document, 'analysis') or not document.analysis.data:
            return []
        
        # Create a mock database manager interface
        class MockDB:
            def get_document(self, doc_id):
                return {
                    'id': document.id,
                    'filename': document.filename,
                    'analysis': document.analysis.data,
                    'cleaned_text': document.content.cleaned_text if hasattr(document, 'content') else ''
                }
        
        search_engine = CorpusSearchEngine(MockDB())
        
        # Execute search based on type
        search_type = search_params.get('search_type', 'word')
        keyword = search_params.get('keyword', '')
        context_size = search_params.get('context_size', 5)
        
        matches = []
        
        if search_type == 'word':
            matches = search_engine.search_word(
                keyword,
                doc_id=document.id,
                regex=search_params.get('regex', False),
                case_sensitive=search_params.get('case_sensitive', False)
            )
        elif search_type == 'lemma':
            matches = search_engine.search_lemma(
                keyword,
                doc_id=document.id,
                case_sensitive=search_params.get('case_sensitive', False)
            )
        elif search_type == 'pos':
            pos_tags = search_params.get('pos_tags', [])
            matches = search_engine.search_pos(pos_tags, doc_id=document.id)
        elif search_type == 'advanced':
            matches = search_engine.complex_query(
                doc_id=document.id,
                word_pattern=search_params.get('word_pattern'),
                lemma=search_params.get('lemma_filter'),
                pos_tags=search_params.get('pos_tags'),
                min_confidence=search_params.get('min_confidence', 0.0),
                max_confidence=search_params.get('max_confidence', 1.0),
                regex=search_params.get('regex', False),
                case_sensitive=search_params.get('case_sensitive', False)
            )
        
        # Get concordance
        if matches:
            concordance = search_engine.get_concordance(
                matches,
                doc_id=document.id,
                context_words=context_size
            )
            return concordance
        
        return []
    
    def get_statistics(self, document):
        """
        Get statistics for a document.
        
        Args:
            document: Document model instance
        
        Returns:
            Dictionary with statistics
        """
        if not hasattr(document, 'analysis') or not document.analysis.data:
            return None
        
        stats = CorpusStatistics(document.analysis.data)
        
        return {
            'token_count': stats.token_count(),
            'type_count': stats.type_count(),
            'ttr': stats.type_token_ratio(),
            'word_frequency': stats.word_frequency(top_n=50),
            'lemma_frequency': stats.lemma_frequency(top_n=50),
            'pos_distribution': stats.pos_distribution(),
            'zipf': stats.zipf_distribution()[:20]
        }
    
    def export_document(self, document, export_format='json', include_structure=False):
        """
        Export document in specified format.
        
        Args:
            document: Document model instance
            export_format: Format (json, csv, conllu, vrt)
            include_structure: Whether to include sentence structure (for VRT)
        
        Returns:
            Exported content as string
        """
        if not hasattr(document, 'analysis') or not document.analysis.data:
            return None
        
        metadata = {
            'id': f'doc{document.id}',
            'filename': document.filename,
            'date': document.upload_date.strftime('%Y-%m-%d'),
            'format': document.format
        }
        
        exporter = CorpusExporter(document.analysis.data, metadata)
        
        if export_format == 'json':
            return exporter.to_json(pretty=True)
        elif export_format == 'csv':
            return exporter.to_csv()
        elif export_format == 'conllu':
            return exporter.to_conllu()
        elif export_format == 'vrt':
            return exporter.to_vrt(include_structure=include_structure)
        
        return None
