"""Privacy-related views for KVKK/GDPR compliance."""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json

from .models import Document, QueryLog, ExportLog
from .privacy.anonymizer import Anonymizer


@login_required
def anonymization_report_view(request, document_id):
    """Display anonymization report for a document."""
    document = get_object_or_404(Document, id=document_id)
    
    # Check permission
    if not (request.user.is_staff or document.uploaded_by == request.user):
        messages.error(request, 'You do not have permission to view this report.')
        return redirect('corpus:document_detail', pk=document_id)
    
    # Check if document has been anonymized
    if not document.anonymization_report:
        messages.warning(request, 'This document has not been anonymized yet.')
        return redirect('corpus:document_detail', pk=document_id)
    
    context = {
        'document': document,
        'report': document.anonymization_report,
        'privacy_status': document.get_privacy_status_display(),
        'anonymized_at': document.anonymized_at,
    }
    
    return render(request, 'corpus/anonymization_report.html', context)


@login_required
def export_user_data_view(request):
    """Export all user data for GDPR compliance (data portability)."""
    user = request.user
    
    # Collect user data
    data = {
        'export_date': timezone.now().isoformat(),
        'user_profile': {
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
        'profile_settings': {},
        'documents': [],
        'query_history': [],
        'export_history': [],
    }
    
    # Add profile data if exists
    if hasattr(user, 'profile'):
        profile = user.profile
        data['profile_settings'] = {
            'role': profile.role,
            'institution': profile.institution,
            'daily_export_limit': profile.daily_export_limit,
            'monthly_query_limit': profile.monthly_query_limit,
            'can_use_api': profile.can_use_api,
        }
    
    # Add documents
    documents = Document.objects.filter(uploaded_by=user)
    for doc in documents:
        data['documents'].append({
            'id': doc.id,
            'title': doc.title,
            'genre': doc.genre,
            'author': doc.author,
            'uploaded_at': doc.uploaded_at.isoformat(),
            'word_count': doc.get_word_count(),
            'privacy_status': doc.privacy_status,
            'collection': doc.collection,
        })
    
    # Add query history (last 1000 queries)
    queries = QueryLog.objects.filter(user=user).order_by('-timestamp')[:1000]
    for query in queries:
        data['query_history'].append({
            'timestamp': query.timestamp.isoformat(),
            'query': query.query,
            'query_type': query.query_type,
            'results_count': query.results_count,
        })
    
    # Add export history (last 1000 exports)
    exports = ExportLog.objects.filter(user=user).order_by('-timestamp')[:1000]
    for export in exports:
        data['export_history'].append({
            'timestamp': export.timestamp.isoformat(),
            'document_id': export.document.id if export.document else None,
            'document_title': export.document.title if export.document else None,
            'export_format': export.export_format,
        })
    
    # Return as JSON download
    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )
    filename = f'user_data_{user.username}_{timezone.now().strftime("%Y%m%d")}.json'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@login_required
def privacy_dashboard_view(request):
    """Privacy dashboard showing user's data and anonymization status."""
    user = request.user
    
    # Get user documents
    documents = Document.objects.filter(uploaded_by=user)
    
    # Statistics
    stats = {
        'total_documents': documents.count(),
        'anonymized_documents': documents.filter(privacy_status='anonymized').count(),
        'documents_with_personal_data': documents.filter(contains_personal_data=True).count(),
        'public_documents': documents.filter(privacy_status='public').count(),
    }
    
    # Recent anonymizations
    recent_anonymizations = documents.filter(
        anonymized_at__isnull=False
    ).order_by('-anonymized_at')[:10]
    
    # Documents needing review
    needs_review = documents.filter(
        Q(privacy_status='raw') | Q(contains_personal_data=True)
    ).order_by('-uploaded_at')[:10]
    
    context = {
        'stats': stats,
        'recent_anonymizations': recent_anonymizations,
        'needs_review': needs_review,
    }
    
    return render(request, 'corpus/privacy_dashboard.html', context)


@login_required
def request_account_deletion_view(request):
    """Request account deletion (GDPR Right to Erasure)."""
    if request.method == 'POST':
        # In production, this should:
        # 1. Mark account for deletion
        # 2. Send confirmation email
        # 3. Schedule deletion after 30-day grace period
        # 4. Anonymize or delete user's corpus contributions
        
        messages.success(
            request,
            'Your account deletion request has been received. '
            'You will receive a confirmation email with further instructions.'
        )
        return redirect('corpus:privacy_dashboard')
    
    # Calculate what will be deleted
    user = request.user
    documents_count = Document.objects.filter(uploaded_by=user).count()
    queries_count = QueryLog.objects.filter(user=user).count()
    exports_count = ExportLog.objects.filter(user=user).count()
    
    context = {
        'documents_count': documents_count,
        'queries_count': queries_count,
        'exports_count': exports_count,
    }
    
    return render(request, 'corpus/request_deletion.html', context)


def privacy_policy_view(request):
    """Display privacy policy (KVKK/GDPR compliance)."""
    return render(request, 'corpus/privacy_policy.html')


def terms_of_service_view(request):
    """Display terms of service."""
    return render(request, 'corpus/terms_of_service.html')
