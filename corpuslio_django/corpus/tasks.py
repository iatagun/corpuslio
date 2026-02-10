"""Celery tasks for async document processing.

DEPRECATED: OCR/analysis tasks removed - platform transformed to corpus query system.
Pre-analyzed corpus files (VRT/CoNLL-U) are imported via management commands.
These tasks are kept for backwards compatibility but should not be used.
"""

from celery import shared_task
from django.conf import settings
import sys
import os

# Legacy imports - kept for backwards compatibility
# OCR orchestrator removed - use corpus import commands instead
try:
    from corpuslio import OllamaOrchestrator
    from corpuslio.groq_client import GroqClient
except (ImportError, ModuleNotFoundError):
    # OCR modules removed - platform is now corpus query only
    OllamaOrchestrator = None
    GroqClient = None

from .models import Document, Content, Analysis, ProcessingTask


@shared_task(bind=True)
def process_document_task(self, document_id, analyze=True, enable_dependencies=False, label_studio=False):
    """
    DEPRECATED: OCR processing removed - platform transformed to corpus query system.
    
    This task is kept for backwards compatibility only.
    To import corpus files, use: python manage.py import_corpus file.conllu
    
    Args:
        document_id: Document model ID
        analyze: Whether to perform linguistic analysis
        enable_dependencies: Whether to perform dependency parsing (CoNLL-U)
        label_studio: Whether to export to Label Studio format
    
    Returns:
        Processing result dictionary
    """
    # Return early with deprecation message
    if OllamaOrchestrator is None:
        return {
            'success': False, 
            'error': 'OCR processing deprecated. Use: python manage.py import_corpus file.conllu'
        }
    
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
        
        # DEPRECATED: OCR orchestrator no longer available
        # Return deprecation error
        task.status = 'FAILED'
        task.error_message = 'OCR processing deprecated. Platform is now corpus query only.'
        task.save()
        
        return {
            'success': False,
            'error': 'OCR processing deprecated. Use: python manage.py import_corpus'
        }
        
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
        
        # Perform dependency parsing if requested
        if enable_dependencies and cleaned_text:
            try:
                task.progress = 85
                task.save()
                
                # Import parser
                from corpus.dependency_parser import get_parser
                
                parser = get_parser()
                
                if parser.is_available():
                    # Parse text with Stanza
                    conllu_str = parser.parse(cleaned_text)
                    
                    if conllu_str:
                        # Save to Analysis
                        analysis, _ = Analysis.objects.get_or_create(document=document)
                        analysis.conllu_data = conllu_str
                        analysis.has_dependencies = True
                        analysis.dependency_parser = 'stanza-tr-2.0'
                        analysis.save()
                        
                        print(f"✅ Dependency parsing completed for document {document_id}")
                    else:
                        print(f"⚠️  Dependency parsing returned no data for document {document_id}")
                else:
                    print(f"⚠️  Stanza not available for document {document_id}")
                    print(parser.get_installation_guide())
                    
            except Exception as e:
                print(f"❌ Dependency parsing failed for document {document_id}: {e}")
                import traceback
                traceback.print_exc()
        
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


# ============================================================
# GDPR/KVKK DATA RETENTION TASKS
# ============================================================

@shared_task
def cleanup_expired_data_exports():
    """
    Periodic task to cleanup expired data export files.
    
    Runs daily at 2 AM (configured in Celery Beat schedule).
    
    KVKK/GDPR Compliance:
    - Data export files are kept for 30 days
    - After expiry, files are deleted and status updated to 'expired'
    - Metadata is retained for audit purposes
    """
    from django.utils import timezone
    from .models import DataExportRequest
    import os
    
    # Find expired exports that are completed but past expiry date
    expired_exports = DataExportRequest.objects.filter(
        status='completed',
        expires_at__lt=timezone.now()
    )
    
    deleted_count = 0
    for export in expired_exports:
        # Delete physical files
        if export.json_file:
            try:
                if os.path.exists(export.json_file.path):
                    os.remove(export.json_file.path)
                export.json_file = None
            except Exception as e:
                print(f"Error deleting JSON file: {e}")
        
        if export.csv_file:
            try:
                if os.path.exists(export.csv_file.path):
                    os.remove(export.csv_file.path)
                export.csv_file = None
            except Exception as e:
                print(f"Error deleting CSV file: {e}")
        
        # Update status
        export.status = 'expired'
        export.save()
        deleted_count += 1
    
    return f'Cleaned up {deleted_count} expired data exports'


@shared_task
def process_pending_deletions():
    """
    Periodic task to process account deletion requests past grace period.
    
    Runs daily at 3 AM (configured in Celery Beat schedule).
    
    KVKK/GDPR Right to be Forgotten:
    - Account deletion has 7-day grace period
    - After grace period, account is permanently deleted or anonymized
    - Irreversible operation
    """
    from django.utils import timezone
    from .models import AccountDeletionRequest
    from .gdpr_services import AccountDeletionService
    
    # Find deletion requests past grace period
    pending_deletions = AccountDeletionRequest.objects.filter(
        status='grace_period',
        grace_period_ends_at__lt=timezone.now()
    )
    
    processed_count = 0
    for deletion_request in pending_deletions:
        try:
            # Process deletion
            deletion_service = AccountDeletionService(deletion_request.user)
            deletion_service.process_deletion(deletion_request)
            processed_count += 1
        except Exception as e:
            # Update status to failed
            deletion_request.status = 'failed'
            deletion_request.error_message = str(e)
            deletion_request.save()
            print(f"Error processing deletion for user {deletion_request.user.id}: {e}")
    
    return f'Processed {processed_count} account deletions'


@shared_task
def cleanup_inactive_accounts():
    """
    Periodic task to cleanup inactive accounts (2+ years).
    
    Runs monthly (1st of month at 4 AM).
    
    KVKK/GDPR Data Minimization:
    - Accounts inactive for 2+ years are flagged
    - Email notification sent before deletion
    - 30-day warning period before automatic deletion
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.contrib.auth import get_user_model
    from django.core.mail import send_mail
    
    User = get_user_model()
    
    # Find accounts inactive for 2+ years
    cutoff_date = timezone.now() - timedelta(days=730)  # 2 years
    inactive_users = User.objects.filter(
        last_login__lt=cutoff_date,
        is_active=True
    ).exclude(
        is_staff=True  # Don't delete staff accounts
    )
    
    notified_count = 0
    for user in inactive_users:
        # Check if already notified (custom flag would be better)
        # For now, just send notification
        try:
            send_mail(
                subject='Hesap İnaktiflik Uyarısı - OCRchestra',
                message=f"""
Sayın {user.username},

OCRchestra hesabınız 2 yıldan fazla süredir kullanılmamaktadır.

KVKK/GDPR veri minimizasyonu kapsamında, hesabınız 30 gün içinde 
otomatik olarak silinecektir.

Hesabınızı korumak için lütfen giriş yapın:
https://ocrchestra.tr/login/

Ya da hesabınızı manuel olarak silmek için:
https://ocrchestra.tr/corpus/gdpr/account-deletion/request/

İyi günler dileriz,
OCRchestra Ekibi
                """,
                from_email='noreply@ocrchestra.tr',
                recipient_list=[user.email],
                fail_silently=True,
            )
            notified_count += 1
        except Exception as e:
            print(f"Error sending notification to {user.email}: {e}")
    
    return f'Sent inactivity notifications to {notified_count} users'

