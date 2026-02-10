"""
Middleware for query logging and rate limit tracking.
"""

from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import QueryLog, UserProfile, ExportLog, Document
import json
import time
import re


class QueryLogMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log all queries and track daily query counts.
    
    This middleware:
    1. Captures query details (user, IP, query params)
    2. Logs execution time
    3. Updates UserProfile.queries_today counter
    4. Records rate limit hits
    """
    
    def process_request(self, request):
        """Store request start time for execution tracking."""
        request._query_log_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """Log query details after response is generated."""
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Only log GET requests to analysis/search views
        if request.method != 'GET':
            return response
        
        # Check if this is a query-related view
        path = request.path
        
        # Skip export endpoints (they have their own ExportLogMiddleware)
        if '/export/' in path or '/download/' in path:
            logger.info(f"[QueryLogMiddleware] Skipping export/download path: {path}")
            return response
        
        loggable_paths = [
            '/analysis/',
            '/library/',
            '/search/',
            '/api/search/',
        ]
        
        if not any(path.startswith(p) for p in loggable_paths):
            logger.info(f"[QueryLogMiddleware] Path not in loggable_paths: {path}")
            return response
        
        logger.info(f"[QueryLogMiddleware] Path matched: {path}, Method: {request.method}")
        
        # Skip if user opted out or is a bot
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        if 'bot' in user_agent.lower() or 'crawler' in user_agent.lower():
            return response
        
        # Collect query data
        user = request.user if request.user.is_authenticated else None
        ip_address = self.get_client_ip(request)
        session_key = request.session.session_key if hasattr(request, 'session') else None
        
        # Get query parameters
        query_text = request.GET.get('query') or request.GET.get('q') or request.GET.get('search', '')
        
        # Check if there are any filter parameters (for library view)
        has_filters = any(request.GET.get(param) for param in ['author', 'genre', 'date', 'tag', 'collection'])
        
        logger.info(f"[QueryLogMiddleware] query_text='{query_text}', has_filters={has_filters}, GET params={dict(request.GET)}")
        
        # Only log if there's actual search activity (not just browsing)
        # For /analysis/ pages - only log if there's a query or filters (not just viewing the document)
        should_log = bool(query_text) or has_filters
        
        if not should_log:
            logger.info(f"[QueryLogMiddleware] Skipping - no search activity")
            return response
        
        logger.info(f"[QueryLogMiddleware] Will create log - condition met")
        
        query_type = self.detect_query_type(request)
        
        # Calculate execution time
        execution_time_ms = 0
        if hasattr(request, '_query_log_start_time'):
            execution_time_ms = int((time.time() - request._query_log_start_time) * 1000)
        
        # Check if rate limited
        rate_limit_hit = getattr(request, 'limited', False)
        
        # Get filter data
        filters_applied = self.extract_filters(request)
        
        # Determine if cached (check for cache header)
        is_cached = response.get('X-Cache-Hit', False) == 'True'
        
        # Get daily query count for user
        daily_query_count = 0
        if user and user.is_authenticated:
            try:
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # Reset if needed (new day)
                profile.reset_query_count_if_needed()
                
                daily_query_count = profile.queries_today
                
                # Update query count ONLY for successful queries (not rate-limited, not superusers)
                # Rate-limited queries should NOT count toward quota (they were rejected)
                # Cached queries still count (user still consumed the resource)
                should_count_query = not rate_limit_hit and not user.is_superuser
                
                if should_count_query:
                    profile.increment_query_count()
                    # Update count AFTER increment for accurate logging
                    daily_query_count = profile.queries_today
                    
                logger.info(f"[QueryLogMiddleware] User={user.username}, Count before={daily_query_count-1 if should_count_query else daily_query_count}, Should count={should_count_query}, Rate limited={rate_limit_hit}")
            except Exception as e:
                logger.warning(f"Failed to update query count: {e}")
        
        # Create log entry
        try:
            log = QueryLog.objects.create(
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                query_text=query_text[:1000],  # Limit to 1000 chars
                query_type=query_type,
                document=None,  # TODO: Extract from view context if available
                filters_applied=filters_applied,
                result_count=0,  # TODO: Extract from response context
                execution_time_ms=execution_time_ms,
                is_cached=is_cached,
                rate_limit_hit=rate_limit_hit,
                daily_query_count=daily_query_count,
            )
            logger.info(f"✅ QueryLog created: ID={log.id}, User={user}, Query='{query_text[:50]}'")
        except Exception as e:
            # Don't crash the request if logging fails
            logger.error(f"❌ Failed to create QueryLog: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return response
    
    def detect_query_type(self, request):
        """Detect query type from request parameters."""
        if 'lemma' in request.GET:
            return 'lemma'
        elif 'pos' in request.GET:
            return 'pos'
        elif 'concordance' in request.path.lower():
            return 'concordance'
        elif 'frequency' in request.path.lower():
            return 'frequency'
        elif 'ngram' in request.path.lower():
            return 'ngram'
        elif request.GET.get('advanced') == 'true':
            return 'advanced'
        else:
            return 'word'
    
    def extract_filters(self, request):
        """Extract filter parameters from request."""
        filters = {}
        filter_params = ['author', 'genre', 'date', 'tag', 'collection', 'language']
        
        for param in filter_params:
            value = request.GET.get(param)
            if value:
                filters[param] = value
        
        return filters
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip[:45] if ip else None  # GenericIPAddressField max length


class ExportLogMiddleware(MiddlewareMixin):
    """
    Middleware to track export downloads and update quotas.
    
    This middleware:
    1. Logs export operations
    2. Updates UserProfile.export_used_mb
    3. Applies watermarks (if configured)
    4. Tracks download counts
    """
    
    def process_response(self, request, response):
        """Log export operations."""
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Only track successful downloads (200, 201, or file responses)
        if response.status_code not in [200, 201]:
            return response
        
        # Check if this is an export/download view
        path = request.path
        if not any(keyword in path.lower() for keyword in ['download', 'export']):
            return response
        
        # Skip watermarked exports (they handle their own logging)
        if '/export/concordance/' in path or '/export/frequency/' in path or '/export/history/' in path:
            logger.info(f"[ExportLogMiddleware] Skipping watermarked export (handles own logging): {path}")
            return response
        
        logger.info(f"[ExportLogMiddleware] Export path matched: {path}")
        
        # Must be authenticated for export tracking
        if not request.user.is_authenticated:
            return response
        
        # Get export metadata from response context (if available)
        export_type = self.detect_export_type(request)
        file_format = self.detect_format(request, response)
        
        # Skip if not a recognized export
        if not export_type:
            logger.info(f"[ExportLogMiddleware] Skipping - no export type detected")
            return response
        
        # Extract document ID from URL if available
        document = self.extract_document(request)
        
        # Get file size from response
        file_size_bytes = len(response.content) if hasattr(response, 'content') else 0
        
        # Get user profile and quota info
        try:
            is_superuser = request.user.is_superuser
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            
            # Reset quota if needed (new month)
            profile.reset_export_quota_if_needed()
            
            quota_before = profile.export_used_mb
            
            # Calculate file size
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            # Update quota ONLY for non-superusers
            if not is_superuser:
                profile.use_export_quota(file_size_mb)
            
            quota_after = profile.export_used_mb
            
            # Create export log for ALL users (including superusers for audit trail)
            log = ExportLog.objects.create(
                user=request.user,
                ip_address=self.get_client_ip(request),
                export_type=export_type,
                format=file_format,
                document=document,
                query_text=request.GET.get('query', '')[:1000],
                row_count=0,  # TODO: Extract from response
                file_size_bytes=file_size_bytes,
                watermark_applied=False,  # Old exports don't have watermarks
                citation_text=self.generate_citation(request),
                quota_before_mb=quota_before,
                quota_after_mb=quota_after,
            )
            logger.info(f"✅ ExportLog created: ID={log.id}, User={request.user}, Type={export_type}, Doc={document.id if document else 'None'}, Size={file_size_mb:.2f}MB")
        except Exception as e:
            logger.error(f"❌ Failed to create ExportLog: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return response
    
    def detect_export_type(self, request):
        """Detect export type from URL path."""
        path = request.path.lower()
        
        if 'concordance' in path:
            return 'concordance'
        elif 'frequency' in path:
            return 'frequency'
        elif 'ngram' in path:
            return 'ngram'
        elif 'statistics' in path or 'stats' in path:
            return 'statistics'
        elif 'analysis' in path:
            return 'analysis'
        elif '/export/' in path:
            # Old export views (pdf, excel, csv) - default to 'document'
            return 'document'
        else:
            return None
    
    def detect_format(self, request, response):
        """Detect file format from Content-Type or request params."""
        # Check request parameter first
        fmt = request.GET.get('format', '').lower()
        if fmt in ['csv', 'json', 'conllu', 'txt', 'xlsx', 'pdf']:
            return fmt
        
        # Check Content-Type header
        content_type = response.get('Content-Type', '')
        if 'csv' in content_type:
            return 'csv'
        elif 'json' in content_type:
            return 'json'
        elif 'pdf' in content_type:
            return 'pdf'
        elif 'excel' in content_type or 'spreadsheet' in content_type:
            return 'xlsx'
        else:
            return 'txt'
    
    def generate_citation(self, request):
        """Generate citation text for the export."""
        current_date = timezone.now().strftime('%Y-%m-%d')
        username = request.user.username if request.user.is_authenticated else 'Anonymous'
        
        return (
            f"CorpusLIO Corpus Platform - "
            f"Export by {username} on {current_date}. "
            f"Please cite: CorpusLIO (2024). Turkish Corpus Analysis Platform. "
            f"Retrieved from https://corpuslio.com"
        )
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip[:45] if ip else None
    
    def extract_document(self, request):
        """Extract document from URL path."""
        # Try to extract document ID from URL path
        # Patterns: /export/pdf/10/, /export/excel/3/, /analysis/10/
        match = re.search(r'/(?:export|analysis)/[^/]+/(\d+)', request.path)
        if match:
            doc_id = int(match.group(1))
            try:
                return Document.objects.get(id=doc_id)
            except Document.DoesNotExist:
                return None
        return None
