"""
Management command to parse documents and add CoNLL-U dependency annotations.

Usage:
    python manage.py parse_dependencies --all
    python manage.py parse_dependencies --doc-id 14
    python manage.py parse_dependencies --doc-id 14 --force
"""

from django.core.management.base import BaseCommand, CommandError
from corpus.models import Document, Analysis
import json
import sys
import os

# Add parent directory to path to import ocrchestra
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))


class Command(BaseCommand):
    help = 'Parse documents and add CoNLL-U dependency annotations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all documents without dependencies',
        )
        parser.add_argument(
            '--doc-id',
            type=int,
            help='Process specific document by ID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Reprocess even if already has dependencies',
        )

    def handle(self, *args, **options):
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS('CoNLL-U Dependency Parser'))
        self.stdout.write("="*70)
        
        # Get documents to process
        if options['doc_id']:
            try:
                documents = [Document.objects.get(id=options['doc_id'])]
                self.stdout.write(f"\n📄 Processing document ID: {options['doc_id']}")
            except Document.DoesNotExist:
                raise CommandError(f"Document with ID {options['doc_id']} does not exist")
        
        elif options['all']:
            if options['force']:
                documents = Document.objects.filter(processed=True)
                self.stdout.write(f"\n📚 Processing ALL {documents.count()} documents (forced)")
            else:
                documents = Document.objects.filter(
                    processed=True,
                    analysis__has_dependencies=False
                ).select_related('analysis')
                self.stdout.write(f"\n📚 Processing {documents.count()} documents without dependencies")
        
        else:
            raise CommandError("Please specify --all or --doc-id")
        
        if not documents:
            self.stdout.write(self.style.WARNING("\n⚠️  No documents to process"))
            return
        
        # Process each document
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for doc in documents:
            self.stdout.write(f"\n{'='*70}")
            self.stdout.write(f"📄 {doc.filename} (ID: {doc.id})")
            
            # Check if already has dependencies
            if hasattr(doc, 'analysis'):
                analysis = doc.analysis
                if analysis.has_dependencies and not options['force']:
                    self.stdout.write(self.style.WARNING("   ⏭️  Already has dependencies (use --force to reprocess)"))
                    skip_count += 1
                    continue
            else:
                # Create analysis if doesn't exist
                analysis = Analysis.objects.create(
                    document=doc,
                    data={
                        'text': 'Auto-generated for dependency parsing',
                        'word_count': 0
                    }
                )
                self.stdout.write("   ✓ Created analysis")
            
            # Try to parse dependencies
            try:
                # Get text from document
                if hasattr(doc, 'content') and doc.content:
                    text = doc.content.cleaned_text or doc.content.raw_text
                else:
                    self.stdout.write(self.style.WARNING("   ⚠️  No text content found"))
                    skip_count += 1
                    continue
                
                if not text or len(text.strip()) < 10:
                    self.stdout.write(self.style.WARNING("   ⚠️  Text too short or empty"))
                    skip_count += 1
                    continue
                
                # Import parser
                from corpus.dependency_parser import get_parser
                
                parser = get_parser()
                
                if not parser.is_available():
                    self.stdout.write(self.style.WARNING(
                        "   ⚠️  Stanza not available"
                    ))
                    self.stdout.write("   💡 Options:")
                    self.stdout.write("      1. Install Stanza: pip install stanza")
                    self.stdout.write("      2. Download model: python -c \"import stanza; stanza.download('tr')\"")
                    skip_count += 1
                    continue
                
                # Parse
                self.stdout.write("   🔄 Parsing...")
                conllu_str = parser.parse(text)
                
                if conllu_str:
                    # Save
                    analysis.conllu_data = conllu_str
                    analysis.has_dependencies = True
                    analysis.dependency_parser = 'stanza-tr-2.0'
                    analysis.save()
                    
                    # Count tokens/sentences
                    token_count = conllu_str.count('\n') - conllu_str.count('\n\n')
                    sentence_count = conllu_str.count('\n\n')
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"   ✅ Parsed {sentence_count} sentences, {token_count} tokens"
                    ))
                    success_count += 1
                else:
                    self.stdout.write(self.style.ERROR("   ❌ Parsing returned no data"))
                    error_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error: {str(e)}"))
                error_count += 1
        
        # Summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("SUMMARY"))
        self.stdout.write("="*70)
        self.stdout.write(f"✅ Successfully processed: {success_count}")
        self.stdout.write(f"⏭️  Skipped: {skip_count}")
        self.stdout.write(f"❌ Errors: {error_count}")
        self.stdout.write(f"📊 Total: {success_count + skip_count + error_count}")
        
        if success_count > 0:
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.SUCCESS("✅ DEPENDENCY PARSING COMPLETE"))
            self.stdout.write("="*70)
            self.stdout.write(f"Access dependency analysis at:")
            self.stdout.write(f"   http://127.0.0.1:8000/dependency/<document_id>/")
        
        if success_count == 0 and error_count == 0 and skip_count > 0:
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.WARNING("INSTALLATION REQUIRED"))
            self.stdout.write("="*70)
            self.stdout.write("To enable automatic dependency parsing:")
            self.stdout.write("")
            self.stdout.write("1️⃣  Install Stanza:")
            self.stdout.write("   pip install stanza")
            self.stdout.write("")
            self.stdout.write("2️⃣  Download Turkish model:")
            self.stdout.write("   python -c \"import stanza; stanza.download('tr')\"")
            self.stdout.write("")
            self.stdout.write("3️⃣  Verify installation:")
            self.stdout.write("   python -c \"import stanza; print(stanza.__version__)\"")
            self.stdout.write("")
            self.stdout.write("4️⃣  Run this command again:")
            self.stdout.write(f"   python manage.py parse_dependencies --all")
