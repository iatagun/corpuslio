import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

from corpus.models import Document, CorpusMetadata

print("--- DOCUMENTS ---")
for doc in Document.objects.all():
    has_meta = CorpusMetadata.objects.filter(document=doc).exists()
    print(f"ID: {doc.id} | File: {doc.filename} | Format: {doc.format} | Processed: {doc.processed} | Has Metadata: {has_meta}")
    if has_meta:
        meta = CorpusMetadata.objects.get(document=doc)
        print(f"  -> Metadata ID: {meta.id} | Sentences: {meta.sentence_count} | Imported At: {meta.imported_at}")

print("\n--- CORPUS METADATA ---")
cnt = CorpusMetadata.objects.count()
print(f"Total Metadata entries: {cnt}")
