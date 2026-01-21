"""Tests for the real OCR expert. Skips when Tesseract or pytesseract not available.
"""
import os
from pathlib import Path
import pytest


try:
    import pytesseract
except Exception:
    pytesseract = None


def _tesseract_available():
    if pytesseract is None:
        return False
    import shutil

    return shutil.which("tesseract") is not None


@pytest.mark.skipif(not _tesseract_available(), reason="Tesseract or pytesseract not available")
def test_real_ocr_on_sample_image(tmp_path):
    from ocrchestra.experts.ocr_expert_real import execute
    from PIL import Image, ImageDraw, ImageFont

    # Create a simple image with text
    img = Image.new("RGB", (200, 60), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 10), "Hello 123", fill=(0, 0, 0))

    path = tmp_path / "sample.png"
    img.save(path)

    res = execute({"document_id": "d1", "image_paths": [str(path)]})
    assert res["document_id"] == "d1"
    assert isinstance(res["ocr"], list)
    assert res["ocr"][0]["text"] is not None
