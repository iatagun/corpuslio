"""API Key authentication for DRF."""

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone
from .models import APIKey


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication.
    
    Clients should authenticate by passing the API key in the request header:
        Authorization: Api-Key YOUR_API_KEY_HERE
    
    Or as a query parameter:
        ?api_key=YOUR_API_KEY_HERE
    """
    
    keyword = 'Api-Key'
    
    def authenticate(self, request):
        """Authenticate the request and return a two-tuple of (user, token)."""
        
        # Try to get API key from header
        api_key_string = self.get_key_from_header(request)
        
        # If not in header, try query parameter
        if not api_key_string:
            api_key_string = request.query_params.get('api_key')
        
        if not api_key_string:
            return None  # No API key provided, try other auth methods
        
        return self.authenticate_credentials(api_key_string, request)
    
    def get_key_from_header(self, request):
        """Extract API key from Authorization header."""
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith(self.keyword):
            return auth_header[len(self.keyword):].strip()
        
        return None
    
    def authenticate_credentials(self, key, request):
        """Validate API key and return user."""
        try:
            api_key = APIKey.objects.select_related('user').get(key=key)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')
        
        # Check if key is active
        if not api_key.is_active:
            raise AuthenticationFailed('API key is inactive')
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < timezone.now():
            raise AuthenticationFailed('API key has expired')
        
        # Check IP restrictions (if configured)
        if api_key.allowed_ips:
            client_ip = self.get_client_ip(request)
            allowed_ips = [ip.strip() for ip in api_key.allowed_ips.split(',')]
            
            if client_ip not in allowed_ips:
                raise AuthenticationFailed(f'API key not allowed from IP: {client_ip}')
        
        # Check quota
        if not api_key.has_quota():
            raise AuthenticationFailed('API key quota exceeded for today')
        
        # Increment usage counter
        api_key.increment_usage()
        
        # Store API key in request for later use (e.g., logging)
        request.api_key = api_key
        
        return (api_key.user, api_key)
    
    def authenticate_header(self, request):
        """Return a string to use as the value of the WWW-Authenticate header."""
        return self.keyword
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
