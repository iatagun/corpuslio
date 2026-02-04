"""Visualization dashboard view."""

from django.shortcuts import render
from .models import Document, Analysis
from collections import Counter
import json


def dashboard_view(request):
    """Interactive visualization dashboard."""
    
    # Overall corpus stats
    total_docs = Document.objects.count()
    processed_docs = Document.objects.filter(processed=True).count()
    
    # Genre distribution
    genre_counts = {}
    for doc in Document.objects.all():
        if doc.metadata and doc.metadata.get('genre'):
            genre = doc.metadata['genre']
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    # POS distribution across all docs
    all_pos_tags = []
    for analysis in Analysis.objects.all():
        if analysis.data:
            pos_tags = [item.get('pos', 'UNK') for item in analysis.data if isinstance(item, dict)]
            all_pos_tags.extend(pos_tags)
    
    pos_distribution = dict(Counter(all_pos_tags).most_common(15))
    
    # Word count distribution
    word_counts = []
    doc_labels = []
    for doc in Document.objects.filter(processed=True)[:20]:
        word_counts.append(doc.get_word_count())
        doc_labels.append(doc.filename[:30])
    
    # Timeline (if date metadata exists)
    date_counts = {}
    for doc in Document.objects.all():
        if doc.metadata and doc.metadata.get('date'):
            year = doc.metadata['date']
            date_counts[year] = date_counts.get(year, 0) + 1
    
    context = {
        'total_docs': total_docs,
        'processed_docs': processed_docs,
        'genre_data': json.dumps(genre_counts),
        'pos_data': json.dumps(pos_distribution),
        'word_counts': json.dumps(word_counts),
        'doc_labels': json.dumps(doc_labels),
        'date_data': json.dumps(date_counts),
        'active_tab': 'dashboard'
    }
    return render(request, 'corpus/dashboard.html', context)
