"""
Corpus Statistics Dashboard Views.

Provides comprehensive statistics about the entire corpus:
- Total documents, tokens, sentences
- Genre distribution
- Publication year trends
- License types
- Text type breakdown
- Top authors
- Collections overview
"""

from django.shortcuts import render
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncYear
from corpus.models import Document
from collections import defaultdict
import json


def corpus_statistics_view(request):
    """Display comprehensive corpus statistics dashboard."""
    
    # General Statistics
    total_documents = Document.objects.filter(processed=True).count()
    total_tokens = Document.objects.filter(processed=True).aggregate(
        total=Sum('token_count')
    )['total'] or 0
    
    # Count documents with dependencies
    docs_with_dependencies = Document.objects.filter(
        processed=True,
        analysis__has_dependencies=True
    ).count()
    
    # Genre Distribution
    genre_stats = Document.objects.filter(
        processed=True
    ).exclude(
        Q(genre='') | Q(genre__isnull=True)
    ).values('genre').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Text Type Distribution
    text_type_stats = Document.objects.filter(
        processed=True
    ).values('text_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # License Distribution
    license_stats = Document.objects.filter(
        processed=True
    ).values('license').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Publication Year Timeline
    year_stats = Document.objects.filter(
        processed=True,
        publication_year__isnull=False
    ).values('publication_year').annotate(
        count=Count('id')
    ).order_by('publication_year')
    
    # Top Authors (limit to top 10)
    author_stats = Document.objects.filter(
        processed=True
    ).exclude(
        Q(author='') | Q(author__isnull=True)
    ).values('author').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Collection Statistics
    collection_stats = Document.objects.filter(
        processed=True
    ).exclude(
        Q(collection='') | Q(collection__isnull=True)
    ).values('collection').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Grade Level Distribution (for educational corpus)
    grade_stats = Document.objects.filter(
        processed=True
    ).exclude(
        Q(grade_level='') | Q(grade_level__isnull=True)
    ).values('grade_level').annotate(
        count=Count('id')
    ).order_by('grade_level')
    
    # Region Distribution
    region_stats = Document.objects.filter(
        processed=True
    ).exclude(
        Q(region='') | Q(region__isnull=True)
    ).values('region').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Recent Additions (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_documents = Document.objects.filter(
        upload_date__gte=thirty_days_ago,
        processed=True
    ).count()
    
    # Calculate average document length
    avg_tokens = total_tokens / total_documents if total_documents > 0 else 0
    
    # Format data for Chart.js
    chart_data = {
        'genre_labels': [item['genre'] for item in genre_stats],
        'genre_counts': [item['count'] for item in genre_stats],
        
        'text_type_labels': [
            _get_text_type_label(item['text_type'])
            for item in text_type_stats
        ],
        'text_type_counts': [item['count'] for item in text_type_stats],
        
        'license_labels': [
            _get_license_label(item['license'])
            for item in license_stats
        ],
        'license_counts': [item['count'] for item in license_stats],
        
        'year_labels': [str(item['publication_year']) for item in year_stats],
        'year_counts': [item['count'] for item in year_stats],
        
        'author_labels': [item['author'][:30] for item in author_stats],  # Truncate long names
        'author_counts': [item['count'] for item in author_stats],
        
        'collection_labels': [item['collection'] for item in collection_stats],
        'collection_counts': [item['count'] for item in collection_stats],
        
        'grade_labels': [item['grade_level'] for item in grade_stats],
        'grade_counts': [item['count'] for item in grade_stats],
        
        'region_labels': [item['region'] for item in region_stats],
        'region_counts': [item['count'] for item in region_stats],
    }
    
    context = {
        'total_documents': total_documents,
        'total_tokens': total_tokens,
        'avg_tokens': int(avg_tokens),
        'docs_with_dependencies': docs_with_dependencies,
        'recent_documents': recent_documents,
        
        'genre_stats': list(genre_stats),
        'text_type_stats': list(text_type_stats),
        'license_stats': list(license_stats),
        'author_stats': list(author_stats),
        'collection_stats': list(collection_stats),
        'grade_stats': list(grade_stats),
        'region_stats': list(region_stats),
        
        'chart_data_json': json.dumps(chart_data),
        'active_tab': 'statistics',
    }
    
    return render(request, 'corpus/corpus_statistics.html', context)


def _get_text_type_label(text_type):
    """Get Turkish label for text_type."""
    labels = {
        'written': 'Yazılı',
        'spoken': 'Sözlü',
        'mixed': 'Karma',
        'web': 'Web/Dijital',
    }
    return labels.get(text_type, text_type)


def _get_license_label(license_code):
    """Get Turkish label for license."""
    labels = {
        'public_domain': 'Kamu Malı',
        'cc_by': 'CC BY',
        'cc_by_sa': 'CC BY-SA',
        'cc_by_nc': 'CC BY-NC',
        'cc_by_nc_sa': 'CC BY-NC-SA',
        'educational': 'Eğitim Amaçlı',
        'copyright': 'Telif Hakkı Korumalı',
        'unknown': 'Bilinmiyor',
    }
    return labels.get(license_code, license_code)
