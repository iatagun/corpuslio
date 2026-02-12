import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'corpuslio_django.settings')
django.setup()

from corpus.models import ExportLog


logs = ExportLog.objects.all().order_by('-created_at')[:10]

print("ID | export_type | watermark_applied | document_id")
print("-" * 70)

for log in logs:
    print(f"{log.id:4} | {log.export_type:15} | {str(log.watermark_applied):5} | {str(log.document_id):10}")
