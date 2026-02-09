"""Test script for imported corpus data."""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ocrchestra_django.settings')
django.setup()

from corpus.models import Document, Sentence, Token, CorpusMetadata

# Get the imported document
doc = Document.objects.get(id=15)

print("=" * 60)
print("IMPORTED CORPUS TEST")
print("=" * 60)
print(f"\n📄 Document: {doc.filename}")
print(f"📊 Author: {doc.author}")
print(f"🏷️  Genre: {doc.genre}")
print(f"🔢 Total Token Count: {doc.token_count}")
print(f"\n📝 Sentences: {doc.sentences.count()}")
print(f"🔤 Tokens: {doc.tokens.count()}")

# Get metadata
try:
    metadata = doc.corpus_metadata
    print(f"\n🗃️  Corpus Metadata:")
    print(f"   Format: {metadata.source_format.upper()}")
    print(f"   Unique Forms: {metadata.unique_forms}")
    print(f"   Unique Lemmas: {metadata.unique_lemmas}")
    print(f"   Imported: {metadata.imported_at.strftime('%Y-%m-%d %H:%M')}")
except:
    print("\n⚠️  No corpus metadata found")

# Show sentences
print(f"\n{'='*60}")
print("SENTENCES:")
print(f"{'='*60}\n")

for sent in doc.sentences.all():
    print(f"{sent.index}. {sent.text}")
    print(f"   Tokens: {sent.token_count}")
    
    # Show first few tokens
    tokens = sent.tokens.all()[:5]
    print(f"   🔍 Token Analysis:")
    for token in tokens:
        print(f"      {token.form:15} | {token.lemma:12} | {token.upos:8} | {token.deprel}")
    
    if sent.tokens.count() > 5:
        print(f"      ... and {sent.tokens.count() - 5} more tokens")
    print()

# Show some statistics
print(f"{'='*60}")
print("LINGUISTIC STATISTICS:")
print(f"{'='*60}\n")

# POS tag distribution
from django.db.models import Count
pos_dist = Token.objects.filter(document=doc).values('upos').annotate(count=Count('upos')).order_by('-count')

print("POS Tag Distribution:")
for pos in pos_dist:
    if pos['upos']:
        print(f"  {pos['upos']:10} : {pos['count']:3}")

# Most frequent forms
print("\nMost Frequent Forms:")
form_dist = Token.objects.filter(document=doc).values('form').annotate(count=Count('form')).order_by('-count')[:10]
for form in form_dist:
    print(f"  {form['form']:15} : {form['count']:3}")

print(f"\n{'='*60}")
print("✅ Test Complete!")
print(f"{'='*60}\n")
