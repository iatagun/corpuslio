"""Visualization dashboard view."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Document, Analysis
from collections import Counter
from datetime import datetime, timedelta
import json


@login_required
def dashboard_view(request):
    """Interactive visualization dashboard with Chart.js."""
    
    # Overall corpus stats
    total_docs = Document.objects.count()
    processed_docs = Document.objects.filter(processed=True).count()
    
    # Upload trend (last 30 days)
    today = datetime.now()
    upload_trend = {}
    for i in range(30, -1, -1):
        date = (today - timedelta(days=i)).strftime('%d/%m')
        upload_trend[date] = 0
    
    # Fill actual upload counts
    for doc in Document.objects.all():
        upload_date = doc.upload_date.strftime('%d/%m')
        if upload_date in upload_trend:
            upload_trend[upload_date] += 1
    
    # Format distribution
    format_counts = {}
    for doc in Document.objects.all():
        ext = doc.filename.split('.')[-1].upper() if '.' in doc.filename else 'UNKNOWN'
        format_counts[ext] = format_counts.get(ext, 0) + 1
    
    # Genre distribution (keeping for compatibility)
    genre_counts = {}
    for doc in Document.objects.all():
        if doc.metadata and doc.metadata.get('genre'):
            genre = doc.metadata['genre']
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    # If no genre data, use format data
    if not genre_counts:
        genre_counts = format_counts
    
    # POS distribution across all docs
    all_pos_tags = []
    for analysis in Analysis.objects.all():
        if analysis.data:
            pos_tags = [item.get('pos', 'UNK') for item in analysis.data if isinstance(item, dict)]
            all_pos_tags.extend(pos_tags)
    
    pos_distribution = dict(Counter(all_pos_tags).most_common(15))
    
    # Word count distribution (top 20 documents)
    word_counts = []
    doc_labels = []
    for doc in Document.objects.filter(processed=True).order_by('-upload_date')[:20]:
        word_count = doc.get_word_count()
        if word_count > 0:  # Only include processed docs with content
            word_counts.append(word_count)
            # Use metadata title if present, otherwise fall back to filename
            title_text = None
            if getattr(doc, 'metadata', None):
                title_text = doc.metadata.get('title') or doc.metadata.get('name')
            if not title_text:
                title_text = getattr(doc, 'filename', 'Untitled')
            # Truncate long titles
            label = title_text[:25] + '...' if len(title_text) > 25 else title_text
            doc_labels.append(label)
    
    # Timeline (if date metadata exists) - otherwise use upload dates
    date_counts = {}
    if Document.objects.filter(metadata__isnull=False).exists():
        for doc in Document.objects.all():
            if doc.metadata and doc.metadata.get('date'):
                year = doc.metadata['date']
                date_counts[year] = date_counts.get(year, 0) + 1
    
    # If no metadata dates, use upload dates grouped by month
    if not date_counts:
        date_counts = upload_trend
    
    context = {
        'total_docs': total_docs,
        'processed_docs': processed_docs,
        'genre_data': json.dumps(genre_counts),
        'pos_data': json.dumps(pos_distribution),
        'word_counts': json.dumps(word_counts),
        'doc_labels': json.dumps(doc_labels),
        'date_data': json.dumps(date_counts),
        'format_data': json.dumps(format_counts),
        'upload_trend': json.dumps(upload_trend),
        'active_tab': 'dashboard'
    }
    return render(request, 'corpus/dashboard.html', context)

