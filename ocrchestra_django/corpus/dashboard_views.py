"""Visualization dashboard view."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.utils import timezone
from .models import Document, Analysis, QueryLog, ExportLog
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


@login_required
def user_dashboard_view(request):
    """Personal user dashboard with activity, statistics and usage data."""
    user = request.user
    now = timezone.now()
    today = now.date()
    thirty_days_ago = now - timedelta(days=30)
    
    # Import API models if available
    try:
        from api.models import APIKey
        has_api = True
    except ImportError:
        has_api = False
    
    # User's documents
    user_docs = Document.objects.filter(uploaded_by=user)
    total_docs = user_docs.count()
    
    # User's queries
    user_queries = QueryLog.objects.filter(user=user)
    total_queries = user_queries.count()
    queries_today = user_queries.filter(timestamp__date=today).count()
    recent_queries = user_queries.order_by('-timestamp')[:10]
    
    # User's exports
    user_exports = ExportLog.objects.filter(user=user)
    total_exports = user_exports.count()
    exports_today = user_exports.filter(timestamp__date=today).count()
    recent_exports = user_exports.order_by('-timestamp')[:10]
    
    # API Keys statistics (if available)
    api_stats = None
    if has_api:
        user_api_keys = APIKey.objects.filter(user=user, is_active=True)
        api_keys_count = user_api_keys.count()
        total_api_requests = sum(key.total_requests for key in user_api_keys)
        api_requests_today = sum(key.requests_today for key in user_api_keys)
        
        api_stats = {
            'keys_count': api_keys_count,
            'total_requests': total_api_requests,
            'requests_today': api_requests_today,
            'recent_keys': user_api_keys.order_by('-created_at')[:5]
        }
    
    # User quotas from profile
    profile = user.userprofile
    quotas = {
        'monthly_query_limit': profile.monthly_query_limit,
        'daily_export_limit': profile.daily_export_limit,
        'queries_this_month': user_queries.filter(
            timestamp__year=today.year,
            timestamp__month=today.month
        ).count(),
        'exports_today': exports_today,
    }
    
    # Query history timeline (last 30 days)
    query_timeline = []
    query_type_counts = Counter()
    
    for i in range(30):
        date = today - timedelta(days=29-i)
        count = user_queries.filter(timestamp__date=date).count()
        query_timeline.append({'date': date.strftime('%Y-%m-%d'), 'count': count})
    
    # Query types distribution
    for query in user_queries.filter(timestamp__gte=thirty_days_ago):
        query_type_counts[query.query_type or 'basic'] += 1
    
    # Export format distribution
    export_format_counts = Counter()
    for export in user_exports.filter(timestamp__gte=thirty_days_ago):
        export_format_counts[export.export_format] += 1
    
    # Recent activity (combined queries + exports + uploads)
    activities = []
    
    # Add recent queries
    for query in user_queries.order_by('-timestamp')[:10]:
        activities.append({
            'type': 'query',
            'timestamp': query.timestamp,
            'description': f"Searched: {query.query[:50]}...",
            'icon': 'search',
            'results': query.results_count
        })
    
    # Add recent exports
    for export in user_exports.order_by('-timestamp')[:10]:
        activities.append({
            'type': 'export',
            'timestamp': export.timestamp,
            'description': f"Exported {export.document.title[:40]} as {export.export_format.upper()}",
            'icon': 'download',
            'format': export.export_format
        })
    
    # Add recent uploads
    for doc in user_docs.order_by('-uploaded_at')[:10]:
        activities.append({
            'type': 'upload',
            'timestamp': doc.uploaded_at,
            'description': f"Uploaded: {doc.title[:50]}",
            'icon': 'upload_file',
            'document': doc.title
        })
    
    # Sort activities by timestamp (most recent first)
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    activities = activities[:30]  # Keep top 30
    
    context = {
        # Summary stats
        'total_docs': total_docs,
        'total_queries': total_queries,
        'total_exports': total_exports,
        'queries_today': queries_today,
        'exports_today': exports_today,
        
        # API stats
        'has_api': has_api,
        'api_stats': api_stats,
        
        # Quotas
        'quotas': quotas,
        'quota_percentage': int((quotas['queries_this_month'] / quotas['monthly_query_limit']) * 100) if quotas['monthly_query_limit'] > 0 else 0,
        'export_percentage': int((quotas['exports_today'] / quotas['daily_export_limit']) * 100) if quotas['daily_export_limit'] > 0 else 0,
        
        # Recent items
        'recent_queries': recent_queries,
        'recent_exports': recent_exports,
        'activities': activities,
        
        # Chart data (JSON serialized)
        'query_timeline': json.dumps(query_timeline),
        'query_types': json.dumps([{'type': k, 'count': v} for k, v in query_type_counts.most_common()]),
        'export_formats': json.dumps([{'format': k, 'count': v} for k, v in export_format_counts.most_common()]),
        
        # User info
        'user_role': profile.role,
        'member_since': user.date_joined,
        
        'active_tab': 'dashboard'
    }
    
    return render(request, 'corpus/user_dashboard.html', context)

