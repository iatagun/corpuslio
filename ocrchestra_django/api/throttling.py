"""Custom throttling for API endpoints based on user tier."""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class APIKeyRateThrottle(UserRateThrottle):
    """
    Throttle based on API key tier.
    
    Rates are configured in settings.py REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    """
    
    def get_cache_key(self, request, view):
        """Use API key as cache key if available."""
        if hasattr(request, 'api_key') and request.api_key:
            # Use API key ID as identifier
            return f'throttle_api_key_{request.api_key.id}'
        
        # Fall back to user-based throttling
        if request.user and request.user.is_authenticated:
            return f'throttle_user_{request.user.pk}'
        
        # Anonymous user (should rarely hit this with API key auth)
        return self.get_ident(request)
    
    def get_rate(self):
        """Get rate based on API key tier."""
        if hasattr(self, 'request') and hasattr(self.request, 'api_key'):
            api_key = self.request.api_key
            tier = api_key.tier
            
            # Map tier to rate
            rate_map = {
                'free': '60/hour',        # 1 per minute
                'standard': '600/hour',   # 10 per minute
                'premium': '3000/hour',   # 50 per minute
                'unlimited': '10000/hour' # Very high (effectively unlimited)
            }
            
            return rate_map.get(tier, '60/hour')
        
        # Default rate for authenticated users without API key
        return '100/hour'
    
    def allow_request(self, request, view):
        """Store request for get_rate() to access."""
        self.request = request
        return super().allow_request(request, view)


class BurstRateThrottle(UserRateThrottle):
    """
    Burst rate throttle to prevent rapid-fire requests.
    Allows short bursts but prevents sustained high-frequency requests.
    """
    scope = 'burst'
    
    def get_rate(self):
        """Burst rate: 10 requests per minute."""
        return '10/min'


class AnonymousAPIThrottle(AnonRateThrottle):
    """Throttle for anonymous API requests (very restrictive)."""
    
    scope = 'anon_api'
    
    def get_rate(self):
        """Anonymous users: 10 requests per day."""
        return '10/day'


class SearchThrottle(UserRateThrottle):
    """
    Throttle specifically for search/concordance endpoints.
    More restrictive than general API throttling.
    """
    scope = 'search'
    
    def get_rate(self):
        """Search rate based on API key tier."""
        if hasattr(self, 'request') and hasattr(self.request, 'api_key'):
            api_key = self.request.api_key
            tier = api_key.tier
            
            rate_map = {
                'free': '30/hour',       # 0.5 per minute
                'standard': '300/hour',  # 5 per minute
                'premium': '1200/hour',  # 20 per minute
                'unlimited': '6000/hour' # 100 per minute
            }
            
            return rate_map.get(tier, '30/hour')
        
        return '50/hour'  # Default for authenticated users
    
    def allow_request(self, request, view):
        """Store request for get_rate() to access."""
        self.request = request
        return super().allow_request(request, view)


class ExportThrottle(UserRateThrottle):
    """
    Throttle for export endpoints.
    Very restrictive to prevent bulk data extraction.
    """
    scope = 'export'
    
    def get_rate(self):
        """Export rate based on API key tier."""
        if hasattr(self, 'request') and hasattr(self.request, 'api_key'):
            api_key = self.request.api_key
            tier = api_key.tier
            
            rate_map = {
                'free': '10/day',
                'standard': '50/day',
                'premium': '200/day',
                'unlimited': '1000/day'
            }
            
            return rate_map.get(tier, '10/day')
        
        return '20/day'  # Default for authenticated users
    
    def allow_request(self, request, view):
        """Store request for get_rate() to access."""
        self.request = request
        return super().allow_request(request, view)
