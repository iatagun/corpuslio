"""
Input validation and sanitization module for OCRchestra

Provides comprehensive validators for:
- File uploads (type, size, content)
- Query inputs (CQP, search terms)
- Form data (user inputs, metadata)
- URL parameters
"""

import os
import re
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import html


# ============================================================
# FILE UPLOAD VALIDATORS
# ============================================================

class FileValidator:
    """Comprehensive file upload validation"""
    
    # Allowed MIME types for each file extension
    ALLOWED_MIMETYPES = {
        '.pdf': ['application/pdf'],
        '.docx': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/zip',  # .docx is actually a zip file
        ],
        '.txt': ['text/plain', 'text/html', 'application/octet-stream'],
        '.png': ['image/png'],
        '.jpg': ['image/jpeg'],
        '.jpeg': ['image/jpeg'],
    }
    
    # Maximum file sizes (bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB for documents
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB for images
    
    def __init__(self, allowed_extensions=None, max_size=None):
        """
        Initialize validator
        
        Args:
            allowed_extensions: List of allowed file extensions (e.g., ['.pdf', '.docx'])
            max_size: Maximum file size in bytes
        """
        self.allowed_extensions = allowed_extensions or getattr(
            settings, 'ALLOWED_DOCUMENT_EXTENSIONS', ['.pdf', '.docx', '.txt']
        )
        self.max_size = max_size or self.MAX_FILE_SIZE
    
    def __call__(self, file):
        """
        Validate uploaded file
        
        Args:
            file: Django UploadedFile object
            
        Raises:
            ValidationError: If validation fails
        """
        # Check file size
        if file.size > self.max_size:
            raise ValidationError(
                _('File too large. Maximum size: %(max_size)s MB'),
                params={'max_size': self.max_size / (1024 * 1024)},
                code='file_too_large'
            )
        
        # Get file extension
        ext = os.path.splitext(file.name)[1].lower()
        
        # Check extension
        if ext not in self.allowed_extensions:
            raise ValidationError(
                _('File type not allowed. Allowed types: %(types)s'),
                params={'types': ', '.join(self.allowed_extensions)},
                code='invalid_extension'
            )
        
        # Check MIME type (only if python-magic is available)
        if MAGIC_AVAILABLE:
            try:
                # Read first chunk to determine MIME type
                file.seek(0)
                chunk = file.read(2048)
                file.seek(0)
                
                mime = magic.from_buffer(chunk, mime=True)
                
                allowed_mimes = self.ALLOWED_MIMETYPES.get(ext, [])
                if mime not in allowed_mimes:
                    raise ValidationError(
                        _('File MIME type (%(mime)s) does not match extension (%(ext)s)'),
                        params={'mime': mime, 'ext': ext},
                        code='mime_mismatch'
                    )
            except Exception as e:
                # If MIME check fails, skip it
                pass
        
        # Check filename safety
        if not self._is_safe_filename(file.name):
            raise ValidationError(
                _('Filename contains unsafe characters'),
                code='unsafe_filename'
            )
    
    def _is_safe_filename(self, filename):
        """Check if filename is safe (no path traversal, etc.)"""
        # Disallow path separators
        if '/' in filename or '\\' in filename:
            return False
        
        # Disallow parent directory references
        if '..' in filename:
            return False
        
        # Only allow alphanumeric, spaces, hyphens, underscores, and dots
        if not re.match(r'^[\w\s\-\.]+$', filename):
            return False
        
        return True


def validate_image_file(file):
    """Validate image files specifically"""
    validator = FileValidator(
        allowed_extensions=['.png', '.jpg', '.jpeg'],
        max_size=FileValidator.MAX_IMAGE_SIZE
    )
    validator(file)


def validate_document_file(file):
    """Validate document files specifically"""
    validator = FileValidator(
        allowed_extensions=['.pdf', '.docx', '.txt'],
        max_size=FileValidator.MAX_DOCUMENT_SIZE
    )
    validator(file)


# ============================================================
# QUERY INPUT VALIDATORS
# ============================================================

class CQPQueryValidator:
    """Validate CQP query syntax and prevent injection"""
    
    # Maximum query length
    MAX_QUERY_LENGTH = 1000
    
    # Allowed CQP operators and characters
    ALLOWED_PATTERN = r'^[\[\]\w\s\"\=\&\.\*\^\$\-\|\(\)]+$'
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        r'__.*__',  # Python dunder methods
        r'import\s+',  # Python imports
        r'eval\(',  # eval() calls
        r'exec\(',  # exec() calls
        r'os\.',  # os module access
        r'sys\.',  # sys module access
        r'\.\.',  # Path traversal
    ]
    
    def __call__(self, query):
        """
        Validate CQP query
        
        Args:
            query: CQP query string
            
        Raises:
            ValidationError: If validation fails
        """
        if not query or not isinstance(query, str):
            raise ValidationError(
                _('Query must be a non-empty string'),
                code='invalid_query_type'
            )
        
        # Check length
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValidationError(
                _('Query too long. Maximum length: %(max_length)s characters'),
                params={'max_length': self.MAX_QUERY_LENGTH},
                code='query_too_long'
            )
        
        # Check for allowed characters
        if not re.match(self.ALLOWED_PATTERN, query):
            raise ValidationError(
                _('Query contains invalid characters'),
                code='invalid_characters'
            )
        
        # Check for blocked patterns
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                raise ValidationError(
                    _('Query contains dangerous pattern'),
                    code='dangerous_pattern'
                )


def validate_cqp_query(query):
    """Validate CQP query input"""
    validator = CQPQueryValidator()
    validator(query)


class SearchTermValidator:
    """Validate search terms"""
    
    MAX_TERM_LENGTH = 200
    MIN_TERM_LENGTH = 1
    
    # Allowed characters in search terms
    ALLOWED_PATTERN = r'^[\w\s\-\.\"\']+$'
    
    def __call__(self, term):
        """
        Validate search term
        
        Args:
            term: Search term string
            
        Raises:
            ValidationError: If validation fails
        """
        if not term or not isinstance(term, str):
            raise ValidationError(
                _('Search term must be a non-empty string'),
                code='invalid_term_type'
            )
        
        # Strip whitespace
        term = term.strip()
        
        # Check length
        if len(term) < self.MIN_TERM_LENGTH:
            raise ValidationError(
                _('Search term too short'),
                code='term_too_short'
            )
        
        if len(term) > self.MAX_TERM_LENGTH:
            raise ValidationError(
                _('Search term too long. Maximum length: %(max_length)s'),
                params={'max_length': self.MAX_TERM_LENGTH},
                code='term_too_long'
            )
        
        # Check for allowed characters
        if not re.match(self.ALLOWED_PATTERN, term):
            raise ValidationError(
                _('Search term contains invalid characters'),
                code='invalid_characters'
            )


def validate_search_term(term):
    """Validate search term input"""
    validator = SearchTermValidator()
    validator(term)


# ============================================================
# FORM DATA VALIDATORS
# ============================================================

def sanitize_html(text, allowed_tags=None):
    """
    Sanitize HTML input
    
    Args:
        text: HTML text to sanitize
        allowed_tags: List of allowed HTML tags (default: none)
        
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # For now, escape all HTML
    # In future, could use bleach library for more control
    if allowed_tags is None:
        return html.escape(text)
    
    # If allowed_tags specified, use bleach
    try:
        import bleach
        return bleach.clean(
            text,
            tags=allowed_tags,
            strip=True
        )
    except ImportError:
        # Fallback to escaping all HTML
        return html.escape(text)


def validate_metadata_field(value, field_name=None):
    """
    Validate metadata field value
    
    Args:
        value: Field value
        field_name: Name of the field (for error messages)
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        return
    
    # Convert to string
    value = str(value)
    
    # Maximum length for metadata fields
    MAX_LENGTH = 500
    
    if len(value) > MAX_LENGTH:
        raise ValidationError(
            _('Metadata field "%(field)s" too long. Maximum: %(max)s characters'),
            params={'field': field_name or 'unknown', 'max': MAX_LENGTH},
            code='metadata_too_long'
        )
    
    # Check for dangerous characters
    if re.search(r'[<>]', value):
        raise ValidationError(
            _('Metadata field "%(field)s" contains HTML tags'),
            params={'field': field_name or 'unknown'},
            code='html_in_metadata'
        )


# ============================================================
# URL PARAMETER VALIDATORS
# ============================================================

def validate_integer_param(value, min_value=None, max_value=None, param_name='parameter'):
    """
    Validate integer URL parameter
    
    Args:
        value: Parameter value
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        param_name: Parameter name (for error messages)
        
    Returns:
        Validated integer value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        int_value = int(value)
    except (ValueError, TypeError):
        raise ValidationError(
            _('Parameter "%(param)s" must be an integer'),
            params={'param': param_name},
            code='invalid_integer'
        )
    
    if min_value is not None and int_value < min_value:
        raise ValidationError(
            _('Parameter "%(param)s" must be at least %(min)s'),
            params={'param': param_name, 'min': min_value},
            code='value_too_small'
        )
    
    if max_value is not None and int_value > max_value:
        raise ValidationError(
            _('Parameter "%(param)s" must be at most %(max)s'),
            params={'param': param_name, 'max': max_value},
            code='value_too_large'
        )
    
    return int_value


def validate_choice_param(value, choices, param_name='parameter'):
    """
    Validate choice parameter
    
    Args:
        value: Parameter value
        choices: List of allowed values
        param_name: Parameter name (for error messages)
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if value not in choices:
        raise ValidationError(
            _('Parameter "%(param)s" must be one of: %(choices)s'),
            params={'param': param_name, 'choices': ', '.join(map(str, choices))},
            code='invalid_choice'
        )
    
    return value


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def is_safe_redirect_url(url):
    """
    Check if URL is safe for redirect (prevents open redirect)
    
    Args:
        url: URL to check
        
    Returns:
        True if safe, False otherwise
    """
    if not url:
        return False
    
    # Must be relative URL (starts with /)
    if not url.startswith('/'):
        return False
    
    # Must not be a protocol-relative URL (starts with //)
    if url.startswith('//'):
        return False
    
    # Must not contain @
    if '@' in url:
        return False
    
    return True


def validate_redirect_url(url):
    """
    Validate redirect URL
    
    Args:
        url: URL to validate
        
    Raises:
        ValidationError: If URL is not safe
    """
    if not is_safe_redirect_url(url):
        raise ValidationError(
            _('Invalid redirect URL'),
            code='invalid_redirect'
        )
