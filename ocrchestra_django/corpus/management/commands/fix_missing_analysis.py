from django.core.management.base import BaseCommand
from corpus.models import Document, Content, Analysis, Sentence, Token

class Command(BaseCommand):
    help = 'Create missing Content and Analysis records for processed documents'

    def handle(self, *args, **options):
        docs = Document.objects.filter(processed=True)
        created = 0
        updated = 0
        for doc in docs:
            # Create Content if missing
            if not hasattr(doc, 'content') or not doc.content.cleaned_text:
                sentences = Sentence.objects.filter(document=doc).order_by('index')
                cleaned = '\n\n'.join([s.text for s in sentences if s.text])
                Content.objects.update_or_create(document=doc, defaults={'raw_text': cleaned, 'cleaned_text': cleaned})
                self.stdout.write(f'Content created/updated for doc {doc.id} ({doc.filename})')
                created += 1

            # Create Analysis if missing
            if not hasattr(doc, 'analysis') or not doc.analysis.data:
                analysis_data = []
                sentences = Sentence.objects.filter(document=doc).order_by('index')
                for s_idx, s in enumerate(sentences, start=1):
                    tokens = Token.objects.filter(sentence=s).order_by('index')
                    for t in tokens:
                        analysis_data.append({
                            'word': t.form,
                            'lemma': t.lemma,
                            'pos': t.upos,
                            'xpos': t.xpos if hasattr(t, 'xpos') else '',
                            'feats': t.feats if hasattr(t, 'feats') else '',
                            'sentence_index': s_idx,
                            'token_index': t.index
                        })
                Analysis.objects.update_or_create(document=doc, defaults={'data': analysis_data, 'has_dependencies': False})
                self.stdout.write(f'Analysis created for doc {doc.id} ({doc.filename})')
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'Done. Content created/updated: {created}, Analysis created: {updated}'))
