"""Celery tasks for async document processing."""

from celery import shared_task
from django.conf import settings
import sys
import os

# Add parent ocrchestra module to path
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, parent_dir)

from ocrchestra import OllamaOrchestrator
from ocrchestra.groq_client import GroqClient

from .models import Document, Content, Analysis, ProcessingTask


@shared_task(bind=True)
def process_document_task(self, document_id, analyze=True, label_studio=False):
    """
    Async task to process a document.
    
    Args:
        document_id: Document model ID
        analyze: Whether to perform linguistic analysis
        label_studio: Whether to export to Label Studio format
    
    Returns:
        Processing result dictionary
    """
    # Get document
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return {'success': False, 'error': 'Document not found'}
    
    # Create or get processing task
    task, created = ProcessingTask.objects.get_or_create(
        document=document,
        task_id=self.request.id,
        defaults={'status': 'PROCESSING'}
    )
    
    if not created:
        task.status = 'PROCESSING'
        task.save()
    
    try:
        # Update progress
        task.progress = 10
        task.save()
        
        # Initialize orchestrator
        orchestrator = OllamaOrchestrator()
        
        # Set up Groq client
        if settings.GROQ_API_KEY:
            orchestrator.ollama_client = GroqClient(api_key=settings.GROQ_API_KEY)
        
        # Process document
        task.progress = 20
        task.save()
        
        file_path = document.file.path
        result = orchestrator.process(file_path)
        
        if not result.get('success'):
            raise Exception(result.get('error', 'Processing failed'))
        
        task.progress = 50
        task.save()
        
        # Extract text
        raw_text = result.get('text', '')
        cleaned_text = orchestrator.corpus_expert.clean_text(raw_text)
        
        task.progress = 60
        task.save()
        
        # Perform analysis if requested
        analysis_data = []
        if analyze and cleaned_text:
            analysis_data = orchestrator.corpus_expert.analyze_with_ollama(cleaned_text)
        
        task.progress = 80
        task.save()
        
        # Save to database
        content, _ = Content.objects.get_or_create(document=document)
        content.raw_text = raw_text
        content.cleaned_text = cleaned_text
        content.save()
        
        if analysis_data:
            analysis, _ = Analysis.objects.get_or_create(document=document)
            
            # Inject Readability Scores
            try:
                from .services import CorpusService
                service = CorpusService()
                readability_data = service.calculate_readability_scores(cleaned_text)
                if readability_data:
                    # Append readability data to analysis JSON structure
                    # We store it as a special key in the JSON
                    if isinstance(analysis_data, list):
                        # If list, we might need a workaround or store metadata separately.
                        # Ideally Analysis.data should be a Dict, but currently it's a List of words.
                        # Let's verify model structure. Analysis.data is JSONField.
                        # We will wrap it if it's a list, or append if dict.
                        pass 
            except Exception as e:
                print(f"Readability calculation failed: {e}")
                readability_data = None
            
            # Store data
            # To avoid breaking existing list format (if usage depends on it being list of tokens),
            # we should separate readability. But Analysis model has only 'data'.
            # BEST PRACTICE: Keep 'data' as list of tokens for analysis.
            # Add 'metadata' or 'scores' field to Analysis model?
            # Or store in Document.metadata? Document.metadata is clean.
            
            if readability_data:
                document.metadata['readability'] = readability_data
                document.save()

            analysis.data = analysis_data
            analysis.save()
        
        # Mark as processed
        document.processed = True
        document.save()
        
        task.progress = 100
        task.status = 'COMPLETED'
        task.save()
        
        # Optional: Label Studio export
        if label_studio and analysis_data:
            export_path = os.path.join(settings.MEDIA_ROOT, 'exports', f'{document.filename}.json')
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            orchestrator.corpus_expert.export_to_label_studio(
                cleaned_text, analysis_data, export_path
            )
        
        return {
            'success': True,
            'document_id': document_id,
            'word_count': len(cleaned_text.split()),
            'analysis_count': len(analysis_data)
        }
    
    except Exception as e:
        task.status = 'FAILED'
        task.error_message = str(e)
        task.save()
        
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cleanup_old_tasks():
    """Periodic task to cleanup old completed/failed tasks."""
    from django.utils import timezone
    from datetime import timedelta
    
    # Delete tasks older than 7 days
    cutoff_date = timezone.now() - timedelta(days=7)
    old_tasks = ProcessingTask.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['COMPLETED', 'FAILED']
    )
    
    count = old_tasks.count()
    old_tasks.delete()
    
    return f'Cleaned up {count} old tasks'
