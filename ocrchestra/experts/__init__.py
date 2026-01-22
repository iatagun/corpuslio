"""Expert modules package for OCRchestra.

Each expert is stateless: it exposes an `execute(input_json: dict) -> dict` function
and validates inputs/outputs against JSON schemas.
"""

from .base import ExpertBase
from .pdf_expert import PDFExpert
from .docx_expert import DOCXExpert

__all__ = [
    "ExpertBase",
    "PDFExpert",
    "DOCXExpert",
]
