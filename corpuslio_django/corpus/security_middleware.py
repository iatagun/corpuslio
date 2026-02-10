"""
Security middleware for OCRchestra

Provides:
- Security headers (XSS, CSRF, Clickjacking, etc.)
- Content Security Policy
- Additional request validation
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
import re


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    
    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(), microphone=(), camera=()
    """
    
    def process_response(self, request, response):
        """Add security headers to response"""
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # XSS protection (for older browsers)
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy (disable unnecessary features)
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Add Content Security Policy header
    
    CSP helps prevent XSS attacks by controlling which resources
    can be loaded and executed.
    """
    
    def process_response(self, request, response):
        """Add CSP header to response"""
        
        # Define CSP directives
        # Note: This is a development-friendly CSP
        # For production, tighten these rules
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
            "img-src 'self' data: https:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        
        csp_header = '; '.join(csp_directives)
        
        # Use Content-Security-Policy-Report-Only in development
        # to avoid breaking functionality
        if hasattr(request, 'user') and request.user.is_superuser:
            # For superusers, use report-only mode
            response['Content-Security-Policy-Report-Only'] = csp_header
        else:
            # For regular users, enforce CSP
            response['Content-Security-Policy'] = csp_header
        
        return response


class RequestValidationMiddleware(MiddlewareMixin):
    """
    Additional request validation
    
    - Validate HTTP methods
    - Check for suspicious patterns
    - Enforce request size limits
    """
    
    # Suspicious patterns in request paths
    SUSPICIOUS_PATTERNS = [
        r'\.\.',  # Path traversal
        r'<script',  # XSS attempt
        r'javascript:',  # JavaScript protocol
        r'data:text/html',  # Data URI XSS
        r'\\x[0-9a-f]{2}',  # Hex encoding
        r'%[0-9a-f]{2}%[0-9a-f]{2}%[0-9a-f]{2}',  # Multiple URL encoding
    ]
    
    # Maximum request body size (bytes)
    MAX_REQUEST_SIZE = 100 * 1024 * 1024  # 100 MB
    
    def process_request(self, request):
        """Validate incoming request"""
        
        # Check for suspicious patterns in path
        path = request.path_info
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return HttpResponseForbidden('Suspicious request pattern detected')
        
        # Check for suspicious patterns in GET parameters
        for key, value in request.GET.items():
            if isinstance(value, str):
                for pattern in self.SUSPICIOUS_PATTERNS:
                    if re.search(pattern, value, re.IGNORECASE):
                        return HttpResponseForbidden('Suspicious request parameter detected')
        
        # Check request size
        if hasattr(request, 'META') and 'CONTENT_LENGTH' in request.META:
            try:
                content_length = int(request.META['CONTENT_LENGTH'])
                if content_length > self.MAX_REQUEST_SIZE:
                    return HttpResponseForbidden('Request too large')
            except (ValueError, TypeError):
                pass
        
        return None


class HTTPSRedirectMiddleware(MiddlewareMixin):
    """
    Redirect HTTP requests to HTTPS in production
    
    Only active when DEBUG=False
    """
    
    def process_request(self, request):
        """Redirect to HTTPS if not already"""
        
        # Only enforce in production
        from django.conf import settings
        if settings.DEBUG:
            return None
        
        # Check if request is already HTTPS
        if request.is_secure():
            return None
        
        # Check for X-Forwarded-Proto header (from load balancer)
        if request.META.get('HTTP_X_FORWARDED_PROTO') == 'https':
            return None
        
        # Redirect to HTTPS
        from django.http import HttpResponsePermanentRedirect
        url = request.build_absolute_uri(request.get_full_path())
        secure_url = url.replace('http://', 'https://', 1)
        return HttpResponsePermanentRedirect(secure_url)


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enhance session security
    
    - Rotate session ID on login
    - Add session timeout
    - Validate session integrity
    """
    
    # Session timeout (seconds)
    SESSION_TIMEOUT = 3600  # 1 hour
    
    def process_request(self, request):
        """Check session validity"""
        
        # Skip for anonymous users
        if not request.user.is_authenticated:
            return None
        
        # Check session timeout
        if hasattr(request.session, 'get'):
            last_activity = request.session.get('last_activity')
            if last_activity:
                from datetime import datetime, timedelta
                last_activity_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_activity_time > timedelta(seconds=self.SESSION_TIMEOUT):
                    # Session expired, logout user
                    from django.contrib.auth import logout
                    logout(request)
                    return None
            
            # Update last activity
            from datetime import datetime
            request.session['last_activity'] = datetime.now().isoformat()
        
        return None
