from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from django.conf import settings
from corpus.models import Document
from corpus.parsers import CoNLLUParser, VRTParser
import os


class Command(BaseCommand):
    help = 'Reparse an existing Document from its stored file and populate sentences/tokens/metadata'

    def add_arguments(self, parser):
        parser.add_argument('document_id', type=int, help='ID of the existing Document')
        parser.add_argument('--user', type=str, default='admin', help='Importer username')

    def handle(self, *args, **options):
        doc_id = options['document_id']
        try:
            user = User.objects.get(username=options['user'])
        except User.DoesNotExist:
            raise CommandError(f'User not found: {options["user"]}')

        try:
            document = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            raise CommandError(f'Document not found: {doc_id}')

        # Resolve file path
        file_field = getattr(document, 'file', None)
        if not file_field:
            raise CommandError('Document has no file path stored')

        # FieldFile -> use .name to get stored path
        file_name = file_field.name if hasattr(file_field, 'name') else str(file_field)
        media_root = getattr(settings, 'MEDIA_ROOT', '') or ''
        abs_path = os.path.join(media_root, file_name) if not os.path.isabs(file_name) else file_name
        if not os.path.exists(abs_path):
            raise CommandError(f'File not found at {abs_path}')

        # Determine parser
        fmt = (document.format or '').lower()
        if fmt not in ('conllu', 'vrt'):
            if abs_path.endswith('.conllu') or abs_path.endswith('.conll'):
                fmt = 'conllu'
            elif abs_path.endswith('.vrt'):
                fmt = 'vrt'
            else:
                raise CommandError('Unknown file format; specify Document.format or use supported extension')

        try:
            if fmt == 'conllu':
                parser = CoNLLUParser(abs_path, user=user)
                self.stdout.write('Using CoNLLU parser')
            else:
                parser = VRTParser(abs_path, user=user)
                self.stdout.write('Using VRT parser')

            metadata = parser.import_to_database(document)

            document.processed = True
            document.save()

            self.stdout.write(self.style.SUCCESS('Reparse successful'))
            self.stdout.write(f'Document ID: {document.id} - tokens: {document.token_count}')

        except Exception as e:
            raise CommandError(f'Reparse failed: {e}')
