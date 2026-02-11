"""Utility functions for authentication and email verification (Task 11.3)."""

import re
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def send_verification_email(user, request):
    """
    Generate verification token and send email to user.
    
    Args:
        user: Django User instance
        request: HTTP request object (for building absolute URL)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        # Generate token via UserProfile method
        token = user.profile.generate_verification_token()
        
        # Build verification URL
        verification_path = reverse('corpus:verify_email', kwargs={'token': token})
        verification_url = request.build_absolute_uri(verification_path)
        
        # Email context
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'CorpusLIO',
            'expires_hours': 24,
        }
        
        # Render HTML email
        html_message = render_to_string('emails/verification_email.html', context)
        
        # Plain text fallback
        plain_message = render_to_string('emails/verification_email.txt', context)
        
        # Send email
        send_mail(
            subject='[CorpusLIO] Email Adresinizi Doğrulayın',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email} (token: {token[:8]}...)")
        return (True, None)
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")
        return (False, f"Email gönderilemedi: {str(e)}")


def verify_email_token(token):
    """
    Validate email verification token and activate user.
    
    Args:
        token: Verification token string
    
    Returns:
        tuple: (success: bool, message: str, user: User or None)
    """
    from .models import UserProfile
    
    try:
        # Find user profile with this token
        profile = UserProfile.objects.filter(email_verification_token=token).first()
        
        if not profile:
            return (False, "Geçersiz doğrulama linki. Token bulunamadı.", None)
        
        # Check if already verified
        if profile.email_verified:
            return (False, "Bu email adresi zaten doğrulanmış.", profile.user)
        
        # Check if token is still valid (not expired)
        if not profile.is_email_token_valid():
            return (False, "Doğrulama linki süresi dolmuş. Lütfen yeni bir doğrulama emaili isteyin.", profile.user)
        
        # Mark email as verified and activate user
        profile.mark_email_verified()
        
        logger.info(f"Email verified successfully for user {profile.user.username}")
        return (True, "Email adresiniz başarıyla doğrulandı! Şimdi giriş yapabilirsiniz.", profile.user)
        
    except Exception as e:
        logger.error(f"Error verifying email token: {e}")
        return (False, "Doğrulama işlemi sırasında bir hata oluştu.", None)


def check_password_strength(password):
    """
    Check password strength and return validation result.
    
    Requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character (optional but recommended)
    
    Args:
        password: Password string to validate
    
    Returns:
        tuple: (is_valid: bool, errors: list of str)
    """
    errors = []
    
    # Check minimum length
    if len(password) < 8:
        errors.append("Şifre en az 8 karakter olmalıdır.")
    
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Şifre en az 1 büyük harf içermelidir.")
    
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Şifre en az 1 küçük harf içermelidir.")
    
    # Check for digit
    if not re.search(r'\d', password):
        errors.append("Şifre en az 1 rakam içermelidir.")
    
    # Check for special character (optional - adds to strength)
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        # Not an error, but a warning
        # We won't add this as a hard requirement
        pass
    
    # Check for common weak passwords
    weak_passwords = [
        'password', '12345678', 'qwerty', 'abc12345', 'password1',
        '123456789', 'letmein', 'welcome', 'admin123', 'password123'
    ]
    if password.lower() in weak_passwords:
        errors.append("Bu şifre çok yaygın kullanılıyor. Daha güçlü bir şifre seçin.")
    
    is_valid = len(errors) == 0
    return (is_valid, errors)


def get_password_strength_score(password):
    """
    Calculate password strength score (0-100).
    
    Args:
        password: Password string
    
    Returns:
        int: Strength score (0-100)
    """
    score = 0
    
    # Length score (up to 20 points)
    length = len(password)
    if length >= 8:
        score += min(20, length * 2)
    
    # Character variety (up to 40 points)
    if re.search(r'[a-z]', password):
        score += 10
    if re.search(r'[A-Z]', password):
        score += 10
    if re.search(r'\d', password):
        score += 10
    if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        score += 10
    
    # Complexity score (up to 40 points)
    unique_chars = len(set(password))
    score += min(20, unique_chars * 2)
    
    # Pattern detection (penalty)
    if re.search(r'(.)\1{2,}', password):  # Repeated characters
        score -= 10
    if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):  # Sequential
        score -= 10
    
    return max(0, min(100, score))


def send_password_reset_email(user, request):
    """
    Generate password reset token and send email to user.
    
    Args:
        user: Django User instance
        request: HTTP request object (for building absolute URL)
    
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    try:
        # Generate token via UserProfile method
        token = user.profile.generate_password_reset_token()
        
        # Build reset URL
        reset_path = reverse('corpus:password_reset_confirm', kwargs={'token': token})
        reset_url = request.build_absolute_uri(reset_path)
        
        # Email context
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': 'CorpusLIO',
            'expires_hours': 1,
        }
        
        # Render HTML email
        html_message = render_to_string('emails/password_reset_email.html', context)
        
        # Plain text fallback
        plain_message = render_to_string('emails/password_reset_email.txt', context)
        
        # Send email
        send_mail(
            subject='[CorpusLIO] Şifre Sıfırlama Talebi',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Password reset email sent to {user.email} (token: {token[:8]}...)")
        return (True, None)
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}")
        return (False, f"Email gönderilemedi: {str(e)}")


def verify_password_reset_token(token):
    """
    Validate password reset token.
    
    Args:
        token: Reset token string
    
    Returns:
        tuple: (success: bool, message: str, user: User or None)
    """
    from .models import UserProfile
    
    try:
        # Find user profile with this token
        profile = UserProfile.objects.filter(password_reset_token=token).first()
        
        if not profile:
            return (False, "Geçersiz şifre sıfırlama linki. Token bulunamadı.", None)
        
        # Check if token is still valid (not expired)
        if not profile.is_reset_token_valid():
            return (False, "Şifre sıfırlama linki süresi dolmuş. Lütfen yeni bir talep oluşturun.", None)
        
        logger.info(f"Password reset token validated for user {profile.user.username}")
        return (True, "Token geçerli.", profile.user)
        
    except Exception as e:
        logger.error(f"Error verifying password reset token: {e}")
        return (False, "Doğrulama işlemi sırasında bir hata oluştu.", None)


# ========================================
# Login History & Security Utils (Task 11.15)
# ========================================

def get_client_ip(request):
    """
    Get client IP address from request, handling proxies.
    
    Args:
        request: HTTP request object
    
    Returns:
        str: IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take first IP in chain (client IP)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    
    return ip or '0.0.0.0'


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract device, browser, and OS info.
    
    Args:
        user_agent_string: User agent string from request
    
    Returns:
        dict: {
            'device_type': str,  # Desktop, Mobile, Tablet, Bot
            'browser': str,
            'os': str
        }
    """
    if not user_agent_string:
        return {
            'device_type': 'Unknown',
            'browser': 'Unknown',
            'os': 'Unknown'
        }
    
    ua_lower = user_agent_string.lower()
    
    # Device type detection
    if 'bot' in ua_lower or 'crawler' in ua_lower or 'spider' in ua_lower:
        device_type = 'Bot'
    elif 'mobile' in ua_lower or 'android' in ua_lower or 'iphone' in ua_lower:
        device_type = 'Mobile'
    elif 'tablet' in ua_lower or 'ipad' in ua_lower:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    # Browser detection
    if 'edg/' in ua_lower or 'edge' in ua_lower:
        browser = 'Edge'
    elif 'chrome' in ua_lower and 'edg' not in ua_lower:
        browser = 'Chrome'
    elif 'firefox' in ua_lower:
        browser = 'Firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        browser = 'Safari'
    elif 'opera' in ua_lower or 'opr' in ua_lower:
        browser = 'Opera'
    elif 'msie' in ua_lower or 'trident' in ua_lower:
        browser = 'Internet Explorer'
    else:
        browser = 'Unknown'
    
    # OS detection
    if 'windows' in ua_lower:
        if 'windows nt 10' in ua_lower:
            os = 'Windows 10/11'
        elif 'windows nt 6.3' in ua_lower:
            os = 'Windows 8.1'
        elif 'windows nt 6.2' in ua_lower:
            os = 'Windows 8'
        elif 'windows nt 6.1' in ua_lower:
            os = 'Windows 7'
        else:
            os = 'Windows'
    elif 'mac os x' in ua_lower or 'macos' in ua_lower:
        os = 'macOS'
    elif 'linux' in ua_lower:
        os = 'Linux'
    elif 'android' in ua_lower:
        os = 'Android'
    elif 'iphone' in ua_lower or 'ipad' in ua_lower or 'ios' in ua_lower:
        os = 'iOS'
    else:
        os = 'Unknown'
    
    return {
        'device_type': device_type,
        'browser': browser,
        'os': os
    }


def log_login_attempt(request, user=None, username_attempted='', success=True, 
                      failure_reason='', session_key=''):
    """
    Log a login attempt to LoginHistory model.
    
    Args:
        request: HTTP request object
        user: Django User instance (None if user not found)
        username_attempted: Username/email attempted
        success: True if login successful
        failure_reason: Reason for failure (if not successful)
        session_key: Django session key (for successful logins)
    
    Returns:
        LoginHistory: Created log entry
    """
    from .models import LoginHistory
    
    # Get IP address
    ip_address = get_client_ip(request)
    
    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Parse user agent
    ua_info = parse_user_agent(user_agent)
    
    # Detect suspicious activity (basic heuristics)
    is_suspicious = False
    
    # Check for rapid failed attempts from same IP
    if not success and user:
        from django.utils import timezone
        from datetime import timedelta
        
        # Count failed attempts in last 5 minutes from this IP
        recent_failures = LoginHistory.objects.filter(
            ip_address=ip_address,
            success=False,
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if recent_failures >= 3:
            is_suspicious = True
    
    # Create log entry
    log_entry = LoginHistory.objects.create(
        user=user,
        username_attempted=username_attempted,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason,
        session_key=session_key,
        is_suspicious=is_suspicious,
        device_type=ua_info['device_type'],
        browser=ua_info['browser'],
        os=ua_info['os']
    )
    
    logger.info(f"Login attempt logged: user={username_attempted}, success={success}, "
                f"IP={ip_address}, device={ua_info['device_type']}")
    
    return log_entry
