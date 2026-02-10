"""Django management command to import corpus files (VRT/CoNLL-U)."""

import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from corpus.models import Document
from corpus.parsers import CoNLLUParser, VRTParser


class Command(BaseCommand):
    help = 'Import pre-analyzed corpus files (VRT or CoNLL-U format)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'filepath',
            type=str,
            help='Path to corpus file (.vrt or .conllu)'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['vrt', 'conllu', 'auto'],
            default='auto',
            help='File format (auto-detect from extension if not specified)'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Username of importer (default: admin)'
        )
        parser.add_argument(
            '--title',
            type=str,
            help='Document title (default: filename)'
        )
        parser.add_argument(
            '--author',
            type=str,
            help='Document author'
        )
        parser.add_argument(
            '--genre',
            type=str,
            help='Document genre'
        )
        parser.add_argument(
            '--language',
            type=str,
            default='tr',
            help='Document language (default: tr)'
        )
    
    def handle(self, *args, **options):
        filepath = options['filepath']
        
        # Check file exists
        if not os.path.exists(filepath):
            raise CommandError(f'File not found: {filepath}')
        
        # Auto-detect format
        file_format = options['format']
        if file_format == 'auto':
            if filepath.endswith('.vrt'):
                file_format = 'vrt'
            elif filepath.endswith('.conllu') or filepath.endswith('.conll'):
                file_format = 'conllu'
            else:
                raise CommandError(
                    'Cannot auto-detect format. Use --format vrt or --format conllu'
                )
        
        # Get user
        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError(f'User not found: {options["user"]}')
        
        # Create document
        filename = os.path.basename(filepath)
        title = options.get('title') or filename
        
        self.stdout.write(self.style.SUCCESS(f'Importing: {filename}'))
        self.stdout.write(f'Format: {file_format.upper()}')
        self.stdout.write(f'User: {user.username}')
        
        document = Document.objects.create(
            filename=title,
            format=file_format,
            language=options.get('language', 'tr'),
            author=options.get('author', ''),
            genre=options.get('genre', ''),
            processed=False,
        )
        
        # Parse and import
        try:
            if file_format == 'conllu':
                parser = CoNLLUParser(filepath, user=user)
                self.stdout.write('Parsing CoNLL-U file...')
            else:  # vrt
                parser = VRTParser(filepath, user=user)
                self.stdout.write('Parsing VRT file...')
            
            metadata = parser.import_to_database(document)
            
            # Mark as processed
            document.processed = True
            document.save()
            
            self.stdout.write(self.style.SUCCESS('✓ Import successful!'))
            self.stdout.write('')
            self.stdout.write('Statistics:')
            self.stdout.write(f'  Sentences: {metadata.sentence_count:,}')
            self.stdout.write(f'  Tokens: {document.token_count:,}')
            self.stdout.write(f'  Unique forms: {metadata.unique_forms:,}')
            self.stdout.write(f'  Unique lemmas: {metadata.unique_lemmas:,}')
            self.stdout.write('')
            self.stdout.write(f'Document ID: {document.id}')
            self.stdout.write(f'Title: {document.filename}')
            
            if metadata.global_metadata:
                self.stdout.write('')
                self.stdout.write('Global Metadata:')
                for key, value in metadata.global_metadata.items():
                    self.stdout.write(f'  {key}: {value}')
        
        except ValueError as e:
            document.delete()
            raise CommandError(str(e))
        
        except Exception as e:
            document.delete()
            raise CommandError(f'Import failed: {str(e)}')
