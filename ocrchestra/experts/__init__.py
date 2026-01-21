"""Expert modules package for OCRchestra.

Each expert is stateless: it exposes an `execute(input_json: dict) -> dict` function
and validates inputs/outputs against JSON schemas.

This package contains lightweight stubs for several experts used by the orchestrator.
"""

from .base import ExpertBase

__all__ = [
    "ExpertBase",
    "ocr_expert",
    "verifier_expert",
    "post_correction_expert",
    "routing_expert",
]
