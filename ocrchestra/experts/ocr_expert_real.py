"""Real OCR expert using Tesseract via `pytesseract`.

This expert expects input JSON containing either:
- `image_paths`: list of local filesystem paths to images (preferred), or
- `images_base64`: list of base64-encoded image strings.

Output is deterministic and evidence-based: each page contains `text`, an
average `confidence`, and `bounding_boxes` with per-word confidence and box.

Requirements:
- Python packages: `pillow`, `pytesseract`
- Tesseract binary installed and available in PATH

This module does not perform any network operations.
"""
from __future__ import annotations

import base64
import io
import shutil
from typing import Dict, Any, List

from .base import ExpertBase


try:
    from PIL import Image
except Exception as exc:  # pragma: no cover - dependency
    Image = None

try:
    import importlib
    pytesseract = importlib.import_module("pytesseract")
    Output = getattr(pytesseract, "Output", None)
except Exception:
    pytesseract = None
    Output = None


class OCRRealExpert(ExpertBase):
    input_schema_path = None
    output_schema_path = "ocrchestra/schemas/ocr_result_schema.json"

    @staticmethod
    def _ensure_dependencies():
        if Image is None or pytesseract is None:
            raise RuntimeError("Required dependencies missing: install 'pillow' and 'pytesseract'.")

        # Check for tesseract binary
        if shutil.which("tesseract") is None:
            raise RuntimeError("Tesseract binary not found in PATH. Install Tesseract OCR.")

    @staticmethod
    def _load_image_from_base64(b64: str):
        if Image is None:
            raise RuntimeError("Pillow is not available: install the 'pillow' package to load images.")
        data = base64.b64decode(b64)
        return Image.open(io.BytesIO(data))

    @staticmethod
    def _process_image(img: Any) -> Dict[str, Any]:
        # Ensure pytesseract and Output are available (helps static type checkers and runtime)
        assert pytesseract is not None and Output is not None, "pytesseract or Output not available; install 'pytesseract' and ensure import succeeded."

        # Use pytesseract to produce word-level boxes + confidences
        data = pytesseract.image_to_data(img, output_type=Output.DICT)

        words: List[Dict[str, Any]] = []
        texts: List[str] = []
        confs: List[float] = []

        n = len(data.get("text", []))
        for i in range(n):
            word = (data.get("text", [])[i] or "").strip()
            if not word:
                continue
            try:
                conf = float(data.get("conf", [])[i])
            except Exception:
                conf = 0.0

            left = int(data.get("left", [])[i] or 0)
            top = int(data.get("top", [])[i] or 0)
            width = int(data.get("width", [])[i] or 0)
            height = int(data.get("height", [])[i] or 0)

            texts.append(word)
            confs.append(conf)
            words.append({"text": word, "confidence": conf, "box": [left, top, width, height]})

        full_text = " ".join(texts)
        avg_conf = float(sum(confs) / len(confs)) if confs else 0.0

        return {"text": full_text, "confidence": avg_conf, "bounding_boxes": words}

    @staticmethod
    def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
        OCRRealExpert._ensure_dependencies()

        image_paths = input_json.get("image_paths")
        images_b64 = input_json.get("images_base64")

        if not image_paths and not images_b64:
            raise ValueError("Input must contain 'image_paths' or 'images_base64'.")

        results: List[Dict[str, Any]] = []

        if image_paths:
            for idx, p in enumerate(image_paths, start=1):
                assert Image is not None, "Pillow is not available: install the 'pillow' package to load images."
                img = Image.open(p)
                out = OCRRealExpert._process_image(img)
                results.append({"page": idx, "text": out["text"], "confidence": out["confidence"], "bounding_boxes": out["bounding_boxes"]})

        if images_b64:
            for idx, b64 in enumerate(images_b64, start=1):
                img = OCRRealExpert._load_image_from_base64(b64)
                out = OCRRealExpert._process_image(img)
                results.append({"page": idx, "text": out["text"], "confidence": out["confidence"], "bounding_boxes": out["bounding_boxes"]})

        result = {"document_id": input_json.get("document_id"), "ocr": results}
        OCRRealExpert.validate_output(result)
        return result


def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
    return OCRRealExpert.execute(input_json)
