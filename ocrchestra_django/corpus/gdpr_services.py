"""
KVKK/GDPR Compliance Services

Provides:
- User data export (JSON/CSV)
- Account deletion
- Consent management
- Data anonymization
"""

import json
import csv
import io
from datetime import timedelta
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from .models import (
    DataExportRequest, ConsentRecord, AccountDeletionRequest,
    Document, QueryLog, ExportLog, UserProfile
)


class UserDataExportService:
    """Service for exporting user data (KVKK/GDPR compliance)."""
    
    def __init__(self, user):
        """
        Initialize service for a user.
        
        Args:
            user: Django User instance
        """
        self.user = user
    
    def collect_user_data(self):
        """
        Collect all user data from the platform.
        
        Returns:
            dict: All user data
        """
        data = {
            'user_info': self._get_user_info(),
            'profile': self._get_profile(),
            'documents': self._get_documents(),
            'queries': self._get_queries(),
            'exports': self._get_exports(),
            'consents': self._get_consents(),
            'api_keys': self._get_api_keys(),
            'export_metadata': {
                'exported_at': timezone.now().isoformat(),
                'export_version': '1.0',
                'platform': 'OCRchestra Corpus Platform'
            }
        }
        return data
    
    def _get_user_info(self):
        """Get basic user information."""
        return {
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'date_joined': self.user.date_joined.isoformat(),
            'last_login': self.user.last_login.isoformat() if self.user.last_login else None,
            'is_active': self.user.is_active,
            'is_staff': self.user.is_staff,
        }
    
    def _get_profile(self):
        """Get user profile data."""
        try:
            profile = self.user.profile
            return {
                'role': profile.role,
                'institution': profile.institution,
                'department': profile.department,
                'research_area': profile.research_area,
                'verification_status': profile.verification_status,
                'verification_document': profile.verification_document.url if profile.verification_document else None,
                'verified_at': profile.verified_at.isoformat() if profile.verified_at else None,
                'bio': profile.bio,
            }
        except UserProfile.DoesNotExist:
            return {}
    
    def _get_documents(self):
        """Get all user documents."""
        documents = Document.objects.filter(uploaded_by=self.user)
        return [
            {
                'id': doc.id,
                'filename': doc.filename,
                'title': getattr(doc, 'title', ''),
                'uploaded_at': doc.uploaded_at.isoformat() if hasattr(doc, 'uploaded_at') else None,
                'processed': doc.processed,
                'file_size_bytes': doc.file_size_bytes if hasattr(doc, 'file_size_bytes') else None,
                'format': doc.format if hasattr(doc, 'format') else None,
                'language': doc.language if hasattr(doc, 'language') else None,
                'token_count': len(doc.analysis.get('tokens', [])) if doc.analysis else 0,
            }
            for doc in documents
        ]
    
    def _get_queries(self):
        """Get all user queries."""
        queries = QueryLog.objects.filter(user=self.user).order_by('-timestamp')[:1000]
        return [
            {
                'id': query.id,
                'query': query.query,
                'query_type': query.query_type,
                'timestamp': query.timestamp.isoformat(),
                'results_count': query.results_count,
                'execution_time_ms': float(query.execution_time_ms) if query.execution_time_ms else None,
            }
            for query in queries
        ]
    
    def _get_exports(self):
        """Get all user exports."""
        exports = ExportLog.objects.filter(user=self.user).order_by('-created_at')
        return [
            {
                'id': export.id,
                'export_type': export.export_type,
                'format': export.format,
                'created_at': export.created_at.isoformat(),
                'file_size_mb': float(export.file_size_mb),
                'downloaded_at': export.last_download.isoformat() if export.last_download else None,
            }
            for export in exports
        ]
    
    def _get_consents(self):
        """Get all user consents."""
        consents = ConsentRecord.objects.filter(user=self.user)
        return [
            {
                'consent_type': consent.consent_type,
                'consented': consent.consented,
                'consented_at': consent.consented_at.isoformat(),
                'withdrawn_at': consent.withdrawn_at.isoformat() if consent.withdrawn_at else None,
                'policy_version': consent.policy_version,
            }
            for consent in consents
        ]
    
    def _get_api_keys(self):
        """Get user API keys (if any)."""
        try:
            from api.models import APIKey
            api_keys = APIKey.objects.filter(user=self.user)
            return [
                {
                    'name': key.name,
                    'created_at': key.created_at.isoformat(),
                    'last_used': key.last_used.isoformat() if key.last_used else None,
                    'is_active': key.is_active,
                    'rate_limit_tier': key.rate_limit_tier,
                }
                for key in api_keys
            ]
        except ImportError:
            return []
    
    def export_to_json(self, data=None):
        """
        Export user data to JSON format.
        
        Args:
            data: User data dict (if None, will collect)
            
        Returns:
            str: JSON content
        """
        if data is None:
            data = self.collect_user_data()
        
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def export_to_csv(self, data=None):
        """
        Export user data to CSV format.
        
        Args:
            data: User data dict (if None, will collect)
            
        Returns:
            dict: CSV files (multiple files for different data types)
        """
        if data is None:
            data = self.collect_user_data()
        
        csv_files = {}
        
        # User info CSV
        csv_files['user_info.csv'] = self._dict_to_csv([data['user_info']])
        
        # Profile CSV
        if data['profile']:
            csv_files['profile.csv'] = self._dict_to_csv([data['profile']])
        
        # Documents CSV
        if data['documents']:
            csv_files['documents.csv'] = self._dict_to_csv(data['documents'])
        
        # Queries CSV
        if data['queries']:
            csv_files['queries.csv'] = self._dict_to_csv(data['queries'])
        
        # Exports CSV
        if data['exports']:
            csv_files['exports.csv'] = self._dict_to_csv(data['exports'])
        
        # Consents CSV
        if data['consents']:
            csv_files['consents.csv'] = self._dict_to_csv(data['consents'])
        
        # API Keys CSV
        if data['api_keys']:
            csv_files['api_keys.csv'] = self._dict_to_csv(data['api_keys'])
        
        return csv_files
    
    def _dict_to_csv(self, data_list):
        """Convert list of dicts to CSV string."""
        if not data_list:
            return ""
        
        output = io.StringIO()
        
        # Get all keys from all dicts (for varying structures)
        all_keys = set()
        for item in data_list:
            all_keys.update(item.keys())
        
        fieldnames = sorted(all_keys)
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data_list)
        
        return output.getvalue()
    
    def create_export_request(self, format='json', ip_address=None, user_agent=None):
        """
        Create a data export request.
        
        Args:
            format: Export format ('json', 'csv', 'both')
            ip_address: Requester IP
            user_agent: Requester user agent
            
        Returns:
            DataExportRequest instance
        """
        request = DataExportRequest.objects.create(
            user=self.user,
            format=format,
            ip_address=ip_address,
            user_agent=user_agent,
            status='pending'
        )
        
        return request
    
    def process_export_request(self, request):
        """
        Process a pending export request.
        
        Args:
            request: DataExportRequest instance
        """
        try:
            request.status = 'processing'
            request.processed_at = timezone.now()
            request.save()
            
            # Collect data
            data = self.collect_user_data()
            
            # Generate files based on format
            if request.format in ['json', 'both']:
                json_content = self.export_to_json(data)
                json_file = ContentFile(json_content.encode('utf-8'))
                filename = f'user_data_{self.user.username}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
                request.json_file.save(filename, json_file, save=False)
            
            if request.format in ['csv', 'both']:
                # For CSV, create a ZIP file with multiple CSVs
                import zipfile
                import tempfile
                
                csv_files = self.export_to_csv(data)
                
                # Create ZIP in memory
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, content in csv_files.items():
                        zip_file.writestr(filename, content)
                
                zip_buffer.seek(0)
                zip_filename = f'user_data_{self.user.username}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.zip'
                request.csv_file.save(zip_filename, ContentFile(zip_buffer.read()), save=False)
            
            # Mark as completed
            request.status = 'completed'
            request.completed_at = timezone.now()
            
            # Set expiry (30 days)
            request.expires_at = timezone.now() + timedelta(days=30)
            
            request.save()
            
        except Exception as e:
            request.status = 'failed'
            request.error_message = str(e)
            request.save()
            raise


class AccountDeletionService:
    """Service for account deletion (KVKK/GDPR Right to be Forgotten)."""
    
    GRACE_PERIOD_DAYS = 7
    
    def __init__(self, user):
        """
        Initialize service for a user.
        
        Args:
            user: Django User instance
        """
        self.user = user
    
    def create_deletion_request(self, deletion_type='full', reason='', ip_address=None):
        """
        Create an account deletion request.
        
        Args:
            deletion_type: 'full' or 'anonymize'
            reason: User's reason for deletion
            ip_address: Requester IP
            
        Returns:
            AccountDeletionRequest instance
        """
        # Get data counts
        documents_count = Document.objects.filter(uploaded_by=self.user).count()
        queries_count = QueryLog.objects.filter(user=self.user).count()
        exports_count = ExportLog.objects.filter(user=self.user).count()
        
        request = AccountDeletionRequest.objects.create(
            user=self.user,
            deletion_type=deletion_type,
            reason=reason,
            ip_address=ip_address,
            status='grace_period',
            grace_period_ends_at=timezone.now() + timedelta(days=self.GRACE_PERIOD_DAYS),
            documents_count=documents_count,
            queries_count=queries_count,
            exports_count=exports_count,
        )
        
        return request
    
    def process_deletion(self, request):
        """
        Process account deletion after grace period.
        
        Args:
            request: AccountDeletionRequest instance
        """
        if request.is_in_grace_period():
            raise ValueError("Cannot delete account during grace period")
        
        request.status = 'processing'
        request.processed_at = timezone.now()
        request.save()
        
        if request.deletion_type == 'full':
            self._full_deletion()
        else:
            self._anonymize_data()
        
        request.status = 'completed'
        request.completed_at = timezone.now()
        request.save()
    
    def _full_deletion(self):
        """Complete account and data deletion."""
        # Delete all user data
        Document.objects.filter(uploaded_by=self.user).delete()
        QueryLog.objects.filter(user=self.user).delete()
        ExportLog.objects.filter(user=self.user).delete()
        ConsentRecord.objects.filter(user=self.user).delete()
        DataExportRequest.objects.filter(user=self.user).delete()
        
        # Delete API keys if exist
        try:
            from api.models import APIKey
            APIKey.objects.filter(user=self.user).delete()
        except ImportError:
            pass
        
        # Delete user profile
        try:
            self.user.profile.delete()
        except UserProfile.DoesNotExist:
            pass
        
        # Delete user account
        self.user.delete()
    
    def _anonymize_data(self):
        """Anonymize user data instead of deletion."""
        # Anonymize username and email
        anonymous_username = f'deleted_user_{self.user.id}'
        anonymous_email = f'deleted_{self.user.id}@anonymous.local'
        
        self.user.username = anonymous_username
        self.user.email = anonymous_email
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.is_active = False
        self.user.save()
        
        # Anonymize profile
        try:
            profile = self.user.profile
            profile.institution = ''
            profile.department = ''
            profile.research_area = ''
            profile.bio = ''
            if profile.verification_document:
                profile.verification_document.delete()
            profile.save()
        except UserProfile.DoesNotExist:
            pass
        
        # Keep documents but mark as anonymized
        # (Useful for research data integrity)
        # Documents are kept but ownership is anonymized


class ConsentManagementService:
    """Service for managing user consents."""
    
    def __init__(self, user):
        """
        Initialize service for a user.
        
        Args:
            user: Django User instance
        """
        self.user = user
    
    def record_consent(self, consent_type, consented=True, policy_version='1.0', 
                      ip_address=None, user_agent=None):
        """
        Record or update user consent.
        
        Args:
            consent_type: Type of consent
            consented: Whether user consented
            policy_version: Version of policy
            ip_address: User IP
            user_agent: User agent
            
        Returns:
            ConsentRecord instance
        """
        # Check if consent already exists
        existing = ConsentRecord.objects.filter(
            user=self.user,
            consent_type=consent_type,
            policy_version=policy_version
        ).first()
        
        if existing:
            # Update existing
            existing.consented = consented
            if not consented:
                existing.withdrawn_at = timezone.now()
            existing.save()
            return existing
        else:
            # Create new
            return ConsentRecord.objects.create(
                user=self.user,
                consent_type=consent_type,
                consented=consented,
                policy_version=policy_version,
                ip_address=ip_address,
                user_agent=user_agent,
            )
    
    def get_consent(self, consent_type, policy_version='1.0'):
        """
        Get user's consent status.
        
        Args:
            consent_type: Type of consent
            policy_version: Version of policy
            
        Returns:
            bool: Whether user has consented
        """
        consent = ConsentRecord.objects.filter(
            user=self.user,
            consent_type=consent_type,
            policy_version=policy_version
        ).first()
        
        if consent:
            return consent.consented and consent.withdrawn_at is None
        
        return False
    
    def withdraw_consent(self, consent_type, policy_version='1.0'):
        """
        Withdraw user consent.
        
        Args:
            consent_type: Type of consent
            policy_version: Version of policy
        """
        consent = ConsentRecord.objects.filter(
            user=self.user,
            consent_type=consent_type,
            policy_version=policy_version
        ).first()
        
        if consent:
            consent.withdraw()
    
    def get_all_consents(self):
        """
        Get all user consents.
        
        Returns:
            QuerySet of ConsentRecord
        """
        return ConsentRecord.objects.filter(user=self.user)
