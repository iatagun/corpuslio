"""
KVKK/GDPR Compliance Views

Provides views for:
- User data export
- Account deletion
- Consent management
- Privacy settings
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from .models import DataExportRequest, ConsentRecord, AccountDeletionRequest
from .gdpr_services import (
    UserDataExportService, 
    AccountDeletionService,
    ConsentManagementService
)


# ============================================================
# USER DATA EXPORT VIEWS
# ============================================================

@login_required
@ratelimit(key='user', rate='5/day', method='POST', block=True)
def request_data_export(request):
    """
    User data export request page (KVKK/GDPR compliance).
    
    Users can request:
    - All their personal data
    - JSON or CSV format
    - Download within 30 days
    """
    if request.method == 'POST':
        format_choice = request.POST.get('format', 'json')
        
        # Get user IP and user agent
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create export request
        export_service = UserDataExportService(request.user)
        export_request = export_service.create_export_request(
            format=format_choice,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Process immediately (for small data)
        # For large datasets, use Celery task
        try:
            export_service.process_export_request(export_request)
            messages.success(
                request,
                'Veri ihraç talebiniz oluşturuldu ve işleniyor. İndirme sayfasına yönlendiriliyorsunuz.'
            )
        except Exception as e:
            messages.error(request, f'Hata: {str(e)}')
        
        return redirect('corpus:data_export_list')
    
    # GET request - show form
    context = {
        'active_tab': 'privacy',
        'pending_requests': DataExportRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'processing']
        ).count(),
    }
    return render(request, 'corpus/gdpr/request_data_export.html', context)


@login_required
def data_export_list(request):
    """
    List all user's data export requests.
    """
    exports = DataExportRequest.objects.filter(user=request.user).order_by('-requested_at')
    
    context = {
        'active_tab': 'privacy',
        'exports': exports,
    }
    return render(request, 'corpus/gdpr/data_export_list.html', context)


@login_required
def download_data_export(request, export_id):
    """
    Download data export file.
    
    Args:
        export_id: DataExportRequest ID
    """
    export = get_object_or_404(
        DataExportRequest,
        id=export_id,
        user=request.user,
        status='completed'
    )
    
    # Check if expired
    if export.is_expired():
        messages.error(request, 'Bu veri ihracının süresi dolmuş.')
        return redirect('corpus:data_export_list')
    
    # Track download
    export.mark_downloaded()
    
    # Determine which file to serve
    file_type = request.GET.get('type', 'json')
    
    if file_type == 'json' and export.json_file:
        response = FileResponse(
            export.json_file.open('rb'),
            as_attachment=True,
            filename=f'user_data_{request.user.username}.json'
        )
        response['Content-Type'] = 'application/json'
        return response
    
    elif file_type == 'csv' and export.csv_file:
        response = FileResponse(
            export.csv_file.open('rb'),
            as_attachment=True,
            filename=f'user_data_{request.user.username}.zip'
        )
        response['Content-Type'] = 'application/zip'
        return response
    
    else:
        messages.error(request, 'Dosya bulunamadı.')
        return redirect('corpus:data_export_list')


# ============================================================
# ACCOUNT DELETION VIEWS
# ============================================================

@login_required
@ratelimit(key='user', rate='3/day', method='POST', block=True)
def request_account_deletion(request):
    """
    Account deletion request page (KVKK/GDPR Right to be Forgotten).
    
    Implements:
    - 7-day grace period
    - Full deletion or anonymization
    - Confirmation required
    """
    # Check if user already has pending request
    existing = AccountDeletionRequest.objects.filter(
        user=request.user,
        status__in=['pending', 'grace_period']
    ).first()
    
    if existing:
        context = {
            'active_tab': 'privacy',
            'existing_request': existing,
        }
        return render(request, 'corpus/gdpr/account_deletion_pending.html', context)
    
    if request.method == 'POST':
        deletion_type = request.POST.get('deletion_type', 'full')
        reason = request.POST.get('reason', '')
        confirmation = request.POST.get('confirmation', '')
        
        # Require explicit confirmation
        if confirmation != request.user.username:
            messages.error(
                request,
                'Hesap silme işlemini onaylamak için kullanıcı adınızı doğru yazmalısınız.'
            )
            return redirect('corpus:request_account_deletion')
        
        # Get IP
        ip_address = request.META.get('REMOTE_ADDR')
        
        # Create deletion request
        deletion_service = AccountDeletionService(request.user)
        deletion_request = deletion_service.create_deletion_request(
            deletion_type=deletion_type,
            reason=reason,
            ip_address=ip_address
        )
        
        messages.warning(
            request,
            f'Hesap silme talebiniz oluşturuldu. {AccountDeletionService.GRACE_PERIOD_DAYS} gün içinde '
            'bu talebi iptal edebilirsiniz. Süre sonunda hesabınız kalıcı olarak silinecektir.'
        )
        
        return redirect('corpus:account_deletion_status')
    
    # GET - show form
    # Get user data summary
    from .models import Document, QueryLog, ExportLog
    
    context = {
        'active_tab': 'privacy',
        'documents_count': Document.objects.filter(uploaded_by=request.user).count(),
        'queries_count': QueryLog.objects.filter(user=request.user).count(),
        'exports_count': ExportLog.objects.filter(user=request.user).count(),
        'grace_period_days': AccountDeletionService.GRACE_PERIOD_DAYS,
    }
    return render(request, 'corpus/gdpr/request_account_deletion.html', context)


@login_required
def account_deletion_status(request):
    """
    Show account deletion request status.
    """
    deletion_request = AccountDeletionRequest.objects.filter(
        user=request.user
    ).order_by('-requested_at').first()
    
    context = {
        'active_tab': 'privacy',
        'deletion_request': deletion_request,
    }
    return render(request, 'corpus/gdpr/account_deletion_status.html', context)


@login_required
@require_http_methods(["POST"])
def cancel_account_deletion(request, request_id):
    """
    Cancel pending account deletion request.
    """
    deletion_request = get_object_or_404(
        AccountDeletionRequest,
        id=request_id,
        user=request.user,
        status__in=['pending', 'grace_period']
    )
    
    deletion_request.cancel()
    
    messages.success(request, 'Hesap silme talebiniz iptal edildi.')
    return redirect('corpus:account_deletion_status')


# ============================================================
# CONSENT MANAGEMENT VIEWS
# ============================================================

@login_required
def consent_management(request):
    """
    Manage user consents (KVKK/GDPR).
    
    Users can:
    - View current consents
    - Withdraw consents
    - Update preferences
    """
    if request.method == 'POST':
        consent_service = ConsentManagementService(request.user)
        
        # Get user IP
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Process consent updates
        consent_types = [
            'data_processing',
            'marketing',
            'third_party',
            'analytics',
        ]
        
        for consent_type in consent_types:
            consented = request.POST.get(consent_type) == 'on'
            consent_service.record_consent(
                consent_type=consent_type,
                consented=consented,
                ip_address=ip_address,
                user_agent=user_agent
            )
        
        messages.success(request, 'İzin tercihleriniz güncellendi.')
        return redirect('corpus:consent_management')
    
    # GET - show current consents
    consent_service = ConsentManagementService(request.user)
    
    consents = {
        'data_processing': consent_service.get_consent('data_processing'),
        'marketing': consent_service.get_consent('marketing'),
        'third_party': consent_service.get_consent('third_party'),
        'analytics': consent_service.get_consent('analytics'),
    }
    
    consent_history = consent_service.get_all_consents()
    
    context = {
        'active_tab': 'privacy',
        'consents': consents,
        'consent_history': consent_history,
    }
    return render(request, 'corpus/gdpr/consent_management.html', context)


# ============================================================
# PRIVACY SETTINGS VIEWS
# ============================================================

@login_required
def privacy_settings(request):
    """
    Privacy settings dashboard.
    
    Central hub for:
    - Data export
    - Account deletion
    - Consent management
    - Privacy policy
    """
    context = {
        'active_tab': 'privacy',
        'pending_exports': DataExportRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'processing']
        ).count(),
        'completed_exports': DataExportRequest.objects.filter(
            user=request.user,
            status='completed'
        ).count(),
        'deletion_request': AccountDeletionRequest.objects.filter(
            user=request.user,
            status__in=['pending', 'grace_period']
        ).first(),
    }
    return render(request, 'corpus/gdpr/privacy_settings.html', context)


# ============================================================
# STATIC PAGES
# ============================================================

def privacy_policy(request):
    """Privacy policy page."""
    context = {
        'policy_version': '1.0',
        'last_updated': '2026-02-09',
    }
    return render(request, 'corpus/gdpr/privacy_policy.html', context)


def terms_of_service(request):
    """Terms of service page."""
    context = {
        'terms_version': '1.0',
        'last_updated': '2026-02-09',
    }
    return render(request, 'corpus/gdpr/terms_of_service.html', context)


def kvkk_notice(request):
    """KVKK (Turkish GDPR) notice page."""
    context = {
        'notice_version': '1.0',
        'last_updated': '2026-02-09',
    }
    return render(request, 'corpus/gdpr/kvkk_notice.html', context)
