"""Create sample tags for testing."""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'corpuslio_django'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corpuslio_django.settings')
django.setup()

from corpus.models import Tag, Document
from django.utils.text import slugify

# Sample tags to create
sample_tags = [
    {'name': 'Edebiyat', 'color': 'blue'},
    {'name': 'Şiir', 'color': 'purple'},
    {'name': 'Roman', 'color': 'green'},
    {'name': 'Tarih', 'color': 'orange'},
    {'name': 'Bilim', 'color': 'teal'},
    {'name': 'Felsefe', 'color': 'pink'},
    {'name': 'Deneme', 'color': 'yellow'},
    {'name': 'Klasik', 'color': 'red'},
]

print("Creating sample tags...")
created_count = 0

for tag_data in sample_tags:
    tag, created = Tag.objects.get_or_create(
        name=tag_data['name'],
        defaults={
            'slug': slugify(tag_data['name']),
            'color': tag_data['color'],
            'description': f"{tag_data['name']} kategorisindeki belgeler"
        }
    )
    if created:
        created_count += 1
        print(f"✓ Created tag: {tag.name} ({tag.color})")
    else:
        print(f"- Tag already exists: {tag.name}")

print(f"\nTotal tags created: {created_count}/{len(sample_tags)}")

# Optionally add tags to some documents
if Document.objects.exists():
    print("\nAdding tags to first 5 documents...")
    docs = Document.objects.all()[:5]
    tags = list(Tag.objects.all()[:3])  # Get first 3 tags
    
    for doc in docs:
        for tag in tags:
            doc.tags.add(tag)
        print(f"✓ Added {len(tags)} tags to: {doc.filename}")

print("\nDone!")
