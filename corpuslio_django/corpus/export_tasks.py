"""Async export tasks for corpus analysis results.

These tasks replace synchronous export views for large dataset exports,
preventing request timeouts and improving user experience with async processing.
"""

from celery import shared_task
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
import os
import tempfile
from decimal import Decimal

from corpus.models import Document, ExportLog, UserProfile, CorpusMetadata
from corpus.query_engine import CorpusQueryEngine
from corpus.collections import Collection as CollectionService
from corpus.corpus_export_utils import (
    export_concordance_csv,
    export_concordance_json,
    export_collocation_csv,
    export_ngram_csv,
    export_frequency_csv,
    generate_citation
)


@shared_task(bind=True, name='corpus.export_tasks.export_concordance_async')
def export_concordance_async_task(self, user_id, search_params, export_format='csv'):
    """
    Async task for concordance export with collection/genre/author filtering.
    
    Args:
        user_id: User ID who requested export
        search_params: Dict with query, search_type, regex, etc.
        export_format: 'csv' or 'json'
    
    Returns:
        dict: Export result with filepath and metadata
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Update task state
        self.update_state(state='PROCESSING', meta={'current': 10, 'total': 100, 'status': 'Filtering documents'})
        
        # Extract search parameters
        query = search_params.get('query', '')
        search_type = search_params.get('search_type', 'form')
        regex = search_params.get('regex', False)
        case_sensitive = search_params.get('case_sensitive', False)
        context_size = search_params.get('context_size', 5)
        limit = search_params.get('limit', 500)
        collection_id = search_params.get('collection_id')
        genre_filter = search_params.get('genre_filter')
        author_filter = search_params.get('author_filter')
        
        # Filter documents
        document_ids = None
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        # Genre/author filtering
        if genre_filter or author_filter:
            meta_query = CorpusMetadata.objects.all()
            if genre_filter:
                meta_query = meta_query.filter(global_metadata__genre__icontains=genre_filter)
            if author_filter:
                meta_query = meta_query.filter(global_metadata__author__icontains=author_filter)
            
            meta_doc_ids = list(meta_query.values_list('document_id', flat=True))
            
            if document_ids:
                document_ids = list(set(document_ids) & set(meta_doc_ids))
            else:
                document_ids = meta_doc_ids
        
        self.update_state(state='PROCESSING', meta={'current': 30, 'total': 100, 'status': 'Executing concordance search'})
        
        # Execute search
        engine = CorpusQueryEngine(documents=document_ids)
        results = engine.concordance(
            query=query,
            context_size=context_size,
            query_type=search_type,
            regex=regex,
            case_sensitive=case_sensitive,
            limit=limit
        )
        
        self.update_state(state='PROCESSING', meta={'current': 70, 'total': 100, 'status': 'Generating export file'})
        
        # Generate export
        if export_format == 'json':
            response = export_concordance_json(results, query, user)
            file_ext = 'json'
        else:
            response = export_concordance_csv(results, query, user)
            file_ext = 'csv'
        
        # Save to temp file
        filename = f"concordance_{query[:20]}_{file_ext}_{self.request.id[:8]}.{file_ext}"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        self.update_state(state='PROCESSING', meta={'current': 95, 'total': 100, 'status': 'Sending notification'})
        
        # Send email notification
        _send_export_ready_email(user, filename, filepath)
        
        return {
            'status': 'COMPLETED',
            'filepath': filepath,
            'filename': filename,
            'result_count': len(results),
            'file_size_mb': round(os.path.getsize(filepath) / (1024 * 1024), 2)
        }
        
    except Exception as exc:
        self.update_state(state='FAILURE', meta={'error': str(exc)})
        raise


@shared_task(bind=True, name='corpus.export_tasks.export_collocation_async')
def export_collocation_async_task(self, user_id, keyword, search_params):
    """
    Async task for collocation export.
    
    Args:
        user_id: User ID
        keyword: Target keyword
        search_params: Dict with window_size, min_freq, collection_id
    """
    try:
        user = User.objects.get(id=user_id)
        
        self.update_state(state='PROCESSING', meta={'current': 20, 'total': 100, 'status': 'Analyzing collocations'})
        
        window_size = search_params.get('window_size', 5)
        min_freq = search_params.get('min_freq', 2)
        collection_id = search_params.get('collection_id')
        
        # Filter documents
        document_ids = None
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        # Execute analysis
        engine = CorpusQueryEngine(documents=document_ids)
        collocates = engine.collocation(
            keyword=keyword,
            window_size=window_size,
            min_frequency=min_freq
        )
        
        self.update_state(state='PROCESSING', meta={'current': 70, 'total': 100, 'status': 'Generating CSV'})
        
        # Export
        response = export_collocation_csv(collocates[:100], keyword, user)
        
        # Save
        filename = f"collocation_{keyword}_{self.request.id[:8]}.csv"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Notify
        _send_export_ready_email(user, filename, filepath)
        
        return {
            'status': 'COMPLETED',
            'filepath': filepath,
            'filename': filename,
            'collocation_count': len(collocates[:100])
        }
        
    except Exception as exc:
        self.update_state(state='FAILURE', meta={'error': str(exc)})
        raise


@shared_task(bind=True, name='corpus.export_tasks.export_ngram_async')
def export_ngram_async_task(self, user_id, search_params):
    """
    Async task for n-gram export with streaming to prevent OOM.
    
    Args:
        user_id: User ID
        search_params: Dict with n, min_freq, use_lemma, collection_id, limit
    """
    try:
        user = User.objects.get(id=user_id)
        
        self.update_state(state='PROCESSING', meta={'current': 20, 'total': 100, 'status': 'Extracting n-grams'})
        
        n = search_params.get('n', 2)
        min_freq = search_params.get('min_freq', 2)
        use_lemma = search_params.get('use_lemma', False)
        collection_id = search_params.get('collection_id')
        limit = search_params.get('limit', 500)
        
        # Filter documents
        document_ids = None
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        # Execute analysis (uses streaming from query_engine.py fix)
        engine = CorpusQueryEngine(documents=document_ids)
        ngrams = engine.ngrams(
            n=n,
            min_frequency=min_freq,
            use_lemma=use_lemma,
            limit=limit
        )
        
        self.update_state(state='PROCESSING', meta={'current': 75, 'total': 100, 'status': 'Generating CSV'})
        
        # Export
        response = export_ngram_csv(ngrams, n, user)
        
        # Save
        filename = f"{n}gram_{self.request.id[:8]}.csv"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Notify
        _send_export_ready_email(user, filename, filepath)
        
        return {
            'status': 'COMPLETED',
            'filepath': filepath,
            'filename': filename,
            'ngram_count': len(ngrams)
        }
        
    except Exception as exc:
        self.update_state(state='FAILURE', meta={'error': str(exc)})
        raise


@shared_task(bind=True, name='corpus.export_tasks.export_frequency_async')
def export_frequency_async_task(self, user_id, search_params):
    """
    Async task for frequency analysis export.
    
    Args:
        user_id: User ID
        search_params: Dict with use_lemma, min_length, collection_id, limit
    """
    try:
        user = User.objects.get(id=user_id)
        
        self.update_state(state='PROCESSING', meta={'current': 30, 'total': 100, 'status': 'Calculating frequencies'})
        
        use_lemma = search_params.get('use_lemma', True)
        min_length = search_params.get('min_length', 1)
        collection_id = search_params.get('collection_id')
        limit = search_params.get('limit', 500)
        
        # Filter documents
        document_ids = None
        if collection_id:
            try:
                collection = CollectionService.objects.get(id=collection_id)
                document_ids = list(collection.documents.values_list('id', flat=True))
            except:
                pass
        
        # Execute analysis
        engine = CorpusQueryEngine(documents=document_ids)
        frequencies = engine.word_frequency(
            use_lemma=use_lemma,
            limit=limit,
            min_length=min_length
        )
        
        self.update_state(state='PROCESSING', meta={'current': 80, 'total': 100, 'status': 'Generating CSV'})
        
        # Export
        response = export_frequency_csv(frequencies, user)
        
        # Save
        filename = f"frequency_{self.request.id[:8]}.csv"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Notify
        _send_export_ready_email(user, filename, filepath)
        
        return {
            'status': 'COMPLETED',
            'filepath': filepath,
            'filename': filename,
            'word_count': len(frequencies)
        }
        
    except Exception as exc:
        self.update_state(state='FAILURE', meta={'error': str(exc)})
        raise


def _send_export_ready_email(user, filename, filepath):
    """Send email notification when export is ready for download."""
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    
    subject = f'[CorpusLIO] Export Hazır: {filename}'
    message = f"""
Sayın {user.get_full_name() or user.username},

Corpus export işleminiz tamamlandı!

Dosya: {filename}
Boyut: {file_size_mb:.2f} MB

Export dosyanızı 24 saat içinde profil sayfanızdan indirebilirsiniz.

İyi çalışmalar,
CorpusLIO Ekibi
    """.strip()
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True  # Don't break task if email fails
        )
    except Exception:
        pass  # Email failure shouldn't break the export task
