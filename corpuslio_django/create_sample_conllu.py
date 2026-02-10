"""
Create sample CoNLL-U document for testing Week 4 features.
"""

import os
import sys
import django

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Add project root to path
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corpuslio_django.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from corpus.models import Document, Analysis
from corpuslio.parsers.conllu_parser import CoNLLUParser

# Sample Turkish CoNLL-U data (3 sentences)
SAMPLE_CONLLU = """# sent_id = 1
# text = Türk dili çok zengindir.
1	Türk	Türk	PROPN	Prop	Case=Nom|Number=Sing	2	nmod	_	_
2	dili	dil	NOUN	Noun	Case=Nom|Number=Sing|Number[psor]=Sing|Person[psor]=3	4	nsubj	_	_
3	çok	çok	ADV	Adverb	_	4	advmod	_	_
4	zengindir	zengin	ADJ	Adj	Aspect=Perf|Mood=Gen|Number=Sing|Person=3|Polarity=Pos|Tense=Pres	0	root	_	SpaceAfter=No
5	.	.	PUNCT	Punc	_	4	punct	_	_

# sent_id = 2
# text = Bu platformu araştırmacılar kullanıyor.
1	Bu	bu	DET	Det	_	2	det	_	_
2	platformu	platform	NOUN	Noun	Case=Acc|Number=Sing	4	obj	_	_
3	araştırmacılar	araştırmacı	NOUN	Noun	Case=Nom|Number=Plur	4	nsubj	_	_
4	kullanıyor	kullan	VERB	Verb	Aspect=Prog|Mood=Ind|Number=Plur|Person=3|Polarity=Pos|Tense=Pres	0	root	_	SpaceAfter=No
5	.	.	PUNCT	Punc	_	4	punct	_	_

# sent_id = 3
# text = Bağımlılık analizleri dilbilimde önemlidir.
1	Bağımlılık	bağımlılık	NOUN	Noun	Case=Nom|Number=Sing	2	nmod	_	_
2	analizleri	analiz	NOUN	Noun	Case=Nom|Number=Plur|Number[psor]=Sing|Person[psor]=3	4	nsubj	_	_
3	dilbilimde	dilbilim	NOUN	Noun	Case=Loc|Number=Sing	4	obl	_	_
4	önemlidir	önemli	ADJ	Adj	Aspect=Perf|Mood=Gen|Number=Sing|Person=3|Polarity=Pos|Tense=Pres	0	root	_	SpaceAfter=No
5	.	.	PUNCT	Punc	_	4	punct	_	_

"""

def create_sample_document():
    """Create a document with CoNLL-U dependency annotations."""
    
    print("="*70)
    print("SAMPLE CONLLU DOCUMENT CREATOR")
    print("="*70)
    
    # Get or create admin user
    try:
        user = User.objects.get(username='admin')
        print(f"\n✓ Using existing user: {user.username}")
    except User.DoesNotExist:
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            print("\n❌ No admin user found. Please create one first with:")
            print("   python manage.py createsuperuser")
            return
        print(f"\n✓ Using superuser: {user.username}")
    
    # Parse CoNLL-U
    print("\n📝 Parsing sample CoNLL-U data...")
    tokens = CoNLLUParser.parse(SAMPLE_CONLLU)
    print(f"   ✓ Parsed {len(tokens)} tokens from 3 sentences")
    
    # Create document
    print("\n📄 Creating document...")
    test_file = SimpleUploadedFile(
        "turkce_bagimlilil_ornegi.txt",
        b"Turk dili cok zengindir. Bu platformu arastirmacilar kullaniyor. Bagimlilik analizleri dilbilimde onemlidir.",
        content_type="text/plain"
    )
    
    document = Document.objects.create(
        filename="turkce_bagimlilil_ornegi.txt",
        file=test_file,
        format="txt",
        author="OCRchestra Team",
        genre="Örnek Metin",
        language="tr",
        processed=True  # Mark as processed
    )
    print(f"   ✓ Document created: ID={document.id}")
    print(f"   ✓ Filename: {document.filename}")
    
    # Create analysis with CoNLL-U data
    print("\n🔬 Creating analysis with dependency annotations...")
    analysis = Analysis.objects.create(
        document=document,
        data={
            'text': 'Türk dili çok zengindir. Bu platformu araştırmacılar kullanıyor. Bağımlılık analizleri dilbilimde önemlidir.',
            'word_count': 15,
            'sentences': 3
        },
        conllu_data=tokens,
        has_dependencies=True,
        dependency_parser='stanza-tr-v2.0'
    )
    print(f"   ✓ Analysis created: ID={analysis.id}")
    print(f"   ✓ Parser: {analysis.dependency_parser}")
    print(f"   ✓ Dependency count: {analysis.get_dependency_count()}")
    
    # Display dependency relations
    print("\n📊 Dependency relations found:")
    relations = analysis.get_dependency_relations()
    for rel, count in sorted(relations.items(), key=lambda x: -x[1])[:10]:
        print(f"   - {rel}: {count}")
    
    print("\n" + "="*70)
    print("✅ SAMPLE DOCUMENT CREATED SUCCESSFULLY!")
    print("="*70)
    print(f"\n🌐 Access the document at:")
    print(f"   http://127.0.0.1:8000/analysis/{document.id}/")
    print(f"\n🔍 Dependency search:")
    print(f"   http://127.0.0.1:8000/dependency/{document.id}/")
    print(f"\n🌳 Dependency tree visualization:")
    print(f"   http://127.0.0.1:8000/dependency/{document.id}/tree/1/")
    print(f"\n📈 Dependency statistics:")
    print(f"   http://127.0.0.1:8000/dependency/{document.id}/statistics/")
    print("\n" + "="*70)
    
    return document

if __name__ == '__main__':
    doc = create_sample_document()
