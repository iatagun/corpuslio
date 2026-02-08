"""
Management command to anonymize documents in bulk.

Usage:
    # Anonymize all documents
    python manage.py anonymize_documents --all
    
    # Anonymize specific document
    python manage.py anonymize_documents --doc-id 10
    
    # Anonymize by collection
    python manage.py anonymize_documents --collection "Basın Metinleri"
    
    # Anonymize only specific entity types
    python manage.py anonymize_documents --all --entity-types EMAIL PHONE TC_ID
    
    # Dry run (don't save changes)
    python manage.py anonymize_documents --all --dry-run
"""

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from corpus.models import Document
from corpus.privacy.anonymizer import Anonymizer
from datetime import datetime


class Command(BaseCommand):
    help = 'Anonymize documents to protect personal data (KVKK/GDPR compliance)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Anonymize all documents'
        )
        parser.add_argument(
            '--doc-id',
            type=int,
            help='Anonymize specific document by ID'
        )
        parser.add_argument(
            '--collection',
            type=str,
            help='Anonymize all documents in specific collection'
        )
        parser.add_argument(
            '--entity-types',
            nargs='+',
            choices=['EMAIL', 'PHONE', 'TC_ID', 'PERSON', 'IP', 'CREDIT_CARD'],
            help='Specific entity types to mask (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview anonymization without saving'
        )
        parser.add_argument(
            '--re-anonymize',
            action='store_true',
            help='Re-anonymize already anonymized documents'
        )
    
    def handle(self, *args, **options):
        anonymizer = Anonymizer()
        
        # Build query
        query = Q()
        
        if options['all']:
            # Anonymize all non-anonymized documents
            if not options['re_anonymize']:
                query &= ~Q(privacy_status='anonymized')
        elif options['doc_id']:
            query &= Q(id=options['doc_id'])
        elif options['collection']:
            query &= Q(collection=options['collection'])
            if not options['re_anonymize']:
                query &= ~Q(privacy_status='anonymized')
        else:
            raise CommandError(
                'Please specify --all, --doc-id, or --collection'
            )
        
        # Get documents
        documents = Document.objects.filter(query).select_related('content')
        total_count = documents.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.WARNING('No documents found to anonymize')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🔍 Found {total_count} documents to anonymize\n')
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('⚠️  DRY RUN MODE - No changes will be saved\n')
            )
        
        # Process documents
        success_count = 0
        error_count = 0
        total_entities = 0
        
        for i, doc in enumerate(documents, 1):
            try:
                self.stdout.write(f'\n[{i}/{total_count}] Processing: {doc.title}')
                
                # Anonymize
                result = anonymizer.anonymize_document(
                    document=doc,
                    entity_types=options['entity_types'],
                    update_content=not options['dry_run']
                )
                
                if result['success']:
                    entities_count = result['entities_count']
                    total_entities += entities_count
                    
                    if entities_count > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'   ✅ Anonymized {entities_count} entities'
                            )
                        )
                        
                        # Show entity breakdown
                        if 'report' in result and 'entity_stats' in result['report']:
                            for entity_type, count in result['report']['entity_stats'].items():
                                self.stdout.write(f'      - {entity_type}: {count}')
                    else:
                        self.stdout.write(
                            self.style.WARNING('   ℹ️  No personal data detected')
                        )
                    
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Error: {result.get("error", "Unknown")}')
                    )
                    error_count += 1
            
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Exception: {str(e)}')
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('\n📊 ANONYMIZATION SUMMARY\n'))
        self.stdout.write(f'   Total documents: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'   ✅ Successful: {success_count}'))
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'   ❌ Errors: {error_count}'))
        
        self.stdout.write(f'   🔒 Total entities masked: {total_entities}')
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n⚠️  DRY RUN - No changes were saved')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n✅ All changes saved to database')
            )
        
        self.stdout.write('='*70 + '\n')
