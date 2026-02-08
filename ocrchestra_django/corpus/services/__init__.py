"""
Corpus services package.
"""

from .export_service import ExportService

# Lazy import for legacy service to avoid circular imports
_CorpusService = None

def __getattr__(name):
    """Lazy load CorpusService to avoid import errors."""
    global _CorpusService
    if name == 'CorpusService':
        if _CorpusService is None:
            try:
                from .legacy import CorpusService as _CS
                _CorpusService = _CS
            except ImportError as e:
                # If legacy service can't be imported, return a placeholder
                import warnings
                warnings.warn(f"CorpusService could not be imported: {e}")
                _CorpusService = type('CorpusService', (), {})
        return _CorpusService
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = ['ExportService', 'CorpusService']
