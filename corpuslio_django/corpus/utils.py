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
