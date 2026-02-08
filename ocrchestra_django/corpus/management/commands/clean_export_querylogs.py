"""
Management command to clean up incorrectly logged QueryLog entries.
Removes QueryLog entries created for export operations.
"""

from django.core.management.base import BaseCommand
from corpus.models import QueryLog


class Command(BaseCommand):
    help = 'Clean up QueryLog entries created for export operations'

    def handle(self, *args, **options):
        # Find QueryLog entries with query_text from export operations
        # These would have been created when export URLs were accessed
        
        # Option 1: Delete entries with empty query_text
        empty_query_logs = QueryLog.objects.filter(query_text='')
        count_empty = empty_query_logs.count()
        
        if count_empty > 0:
            self.stdout.write(f"Found {count_empty} QueryLog entries with empty query_text")
            confirm = input("Delete these entries? (yes/no): ")
            if confirm.lower() == 'yes':
                empty_query_logs.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted {count_empty} empty QueryLog entries'))
        
        # Option 2: Delete entries with result_count = 0 (export operations don't set this)
        # But be careful - legitimate queries can also have 0 results
        
        self.stdout.write(self.style.SUCCESS('Cleanup complete!'))
