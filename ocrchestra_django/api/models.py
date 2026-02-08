"""API models for authentication and access control."""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import secrets
import hashlib


class APIKey(models.Model):
    """API key model for programmatic access."""
    
    TIER_CHOICES = [
        ('free', 'Free (1000 requests/day)'),
        ('standard', 'Standard (10,000 requests/day)'),
        ('premium', 'Premium (100,000 requests/day)'),
        ('unlimited', 'Unlimited'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_keys')
    name = models.CharField(max_length=100, help_text='Descriptive name for this API key')
    key = models.CharField(max_length=64, unique=True, editable=False)
    
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    
    # Usage tracking
    requests_today = models.IntegerField(default=0)
    last_request = models.DateTimeField(null=True, blank=True)
    total_requests = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # IP restrictions (optional)
    allowed_ips = models.TextField(blank=True, help_text='Comma-separated IP addresses')
    
    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.tier})"
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_key():
        """Generate a secure random API key."""
        random_string = secrets.token_urlsafe(32)
        return hashlib.sha256(random_string.encode()).hexdigest()
    
    def get_daily_limit(self):
        """Get daily request limit based on tier."""
        limits = {
            'free': 1000,
            'standard': 10000,
            'premium': 100000,
            'unlimited': float('inf'),
        }
        return limits.get(self.tier, 1000)
    
    def has_quota(self):
        """Check if API key has remaining quota for today."""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
        
        return self.requests_today < self.get_daily_limit()
    
    def increment_usage(self):
        """Increment request counters."""
        self.requests_today += 1
        self.total_requests += 1
        self.last_request = timezone.now()
        self.save(update_fields=['requests_today', 'total_requests', 'last_request'])
    
    def reset_daily_counter(self):
        """Reset daily counter (called by scheduled task)."""
        self.requests_today = 0
        self.save(update_fields=['requests_today'])
