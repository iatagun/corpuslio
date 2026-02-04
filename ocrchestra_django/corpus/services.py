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
