"""PDF Expert Module for OCRchestra.

Extracts text from PDF files using PyMuPDF (fitz). Supports:
- Text-based PDFs: Direct text extraction
- Scanned PDFs: Image extraction + vision model OCR (requires llava)
"""
from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import ExpertBase

logger = logging.getLogger(__name__)

# Try to import fitz (PyMuPDF)
try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False
    fitz = None


class PDFExpert(ExpertBase):
    """Expert for extracting text from PDF documents."""

    def __init__(self, ollama_client=None):
        """Initialize PDF expert.

        Args:
            ollama_client: Optional OllamaClient for vision-based OCR
        """
        self.ollama_client = ollama_client

    @staticmethod
    def is_available() -> bool:
        """Check if PyMuPDF is installed."""
        return HAS_FITZ

    def extract_text(
        self,
        pdf_path: Union[str, Path],
        pages: Optional[List[int]] = None,
        use_vision_fallback: bool = True,
    ) -> Dict[str, Any]:
        """Extract text from PDF file.

        Args:
            pdf_path: Path to PDF file
            pages: Specific page numbers to extract (1-indexed). None = all pages
            use_vision_fallback: Use vision model for pages with no text

        Returns:
            Dict with extracted text and metadata
        """
        if not HAS_FITZ:
            return {
                "success": False,
                "error": "PyMuPDF (fitz) yüklü değil. Lütfen: pip install PyMuPDF",
                "text": "",
                "pages": [],
            }

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return {
                "success": False,
                "error": f"PDF dosyası bulunamadı: {pdf_path}",
                "text": "",
                "pages": [],
            }

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            return {
                "success": False,
                "error": f"PDF açılamadı: {e}",
                "text": "",
                "pages": [],
            }

        total_pages = len(doc)
        
        # Determine which pages to process
        if pages is None:
            page_indices = list(range(total_pages))
        else:
            # Convert 1-indexed to 0-indexed
            page_indices = [p - 1 for p in pages if 0 < p <= total_pages]

        extracted_pages = []
        full_text_parts = []

        for idx in page_indices:
            page = doc[idx]
            page_num = idx + 1  # 1-indexed for output
            
            # Try to extract text directly
            text = page.get_text("text").strip()
            
            page_result = {
                "page": page_num,
                "text": text,
                "method": "text_extraction",
                "has_text": bool(text),
            }

            # If no text found, try vision fallback
            if not text and use_vision_fallback and self.ollama_client:
                logger.info("Sayfa %d metin içermiyor, vision model deneniyor...", page_num)
                try:
                    vision_text = self._extract_with_vision(page)
                    if vision_text:
                        page_result["text"] = vision_text
                        page_result["method"] = "vision_ocr"
                        page_result["has_text"] = True
                        text = vision_text
                except Exception as e:
                    logger.warning("Vision OCR başarısız: %s", e)
                    page_result["vision_error"] = str(e)

            extracted_pages.append(page_result)
            if text:
                full_text_parts.append(f"--- Sayfa {page_num} ---\n{text}")

        doc.close()

        return {
            "success": True,
            "file": str(pdf_path),
            "total_pages": total_pages,
            "extracted_pages": len(extracted_pages),
            "pages": extracted_pages,
            "text": "\n\n".join(full_text_parts),
        }

    def _extract_with_vision(self, page) -> str:
        """Extract text from page using vision model.

        Args:
            page: PyMuPDF page object

        Returns:
            Extracted text from vision model
        """
        if not self.ollama_client:
            raise RuntimeError("Vision OCR için OllamaClient gerekli")

        # Render page to image
        mat = fitz.Matrix(2, 2)  # 2x zoom for better quality
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        # Encode as base64
        img_base64 = base64.b64encode(img_data).decode("utf-8")

        # Create prompt for Turkish OCR
        prompt = (
            "Bu görüntüdeki Türkçe metni oku ve aynen yaz. "
            "Görüntüde metin yoksa 'Metin bulunamadı' yaz. "
            "Sadece metni yaz, başka açıklama ekleme."
        )

        # Use ollama client with image
        from .ollama_client import OllamaClient
        
        # Direct API call with base64 image
        import requests
        import json

        payload = {
            "model": "llava",
            "prompt": prompt,
            "images": [img_base64],
            "stream": False,
            "options": {"temperature": 0.1},
        }

        response = requests.post(
            f"{self.ollama_client.host}/api/generate",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json().get("response", "")

    @staticmethod
    def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PDF extraction (stateless expert interface).

        Args:
            input_json: Dict with 'file_path' and optional 'pages'

        Returns:
            Extraction result dict
        """
        file_path = input_json.get("file_path")
        if not file_path:
            return {"success": False, "error": "file_path gerekli"}

        pages = input_json.get("pages")
        
        expert = PDFExpert()
        return expert.extract_text(file_path, pages=pages)


def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
    """Module-level execute function."""
    return PDFExpert.execute(input_json)
