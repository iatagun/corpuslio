"""OCR expert implementation.

This expert attempts to run real OCR using `pytesseract` (preferred) or
`paddleocr` (fallback). For integration with the orchestrator, it accepts the
standard expert input JSON and also supports an optional `page_files` key with
a list of filesystem paths to images for each page.

If OCR engines are not available, the expert returns a schema-conformant
placeholder and a `note` explaining the limitation.
"""
from __future__ import annotations

from typing import Dict, Any, List
from .base import ExpertBase
import statistics
import os


class OCRExpert(ExpertBase):
    input_schema_path = "ocrchestra/schemas/expert_input_schema.json"
    output_schema_path = "ocrchestra/schemas/ocr_result_schema.json"

    @staticmethod
    def _ocr_with_pytesseract(path: str) -> Dict[str, Any]:
        try:
            from PIL import Image
            import pytesseract
        except Exception as exc:
            raise RuntimeError("pytesseract or PIL not available") from exc
        img = Image.open(path)

        # Helper to run tesseract on a PIL image and collect text/boxes/conf
        def run_tesseract(pil_img):
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            boxes: List[List[int]] = []
            confs: List[float] = []
            text_pieces: List[str] = []
            n = len(data.get("text", []))
            for i in range(n):
                w = data.get("text", [])[i]
                if not w or w.strip() == "":
                    continue
                conf = data.get("conf", [])[i]
                try:
                    conf_val = float(conf)
                except Exception:
                    conf_val = -1.0
                if conf_val >= 0:
                    confs.append(conf_val / 100.0)
                x = int(data.get("left", [])[i])
                y = int(data.get("top", [])[i])
                w_box = int(data.get("width", [])[i])
                h_box = int(data.get("height", [])[i])
                boxes.append([x, y, x + w_box, y + h_box])
                text_pieces.append(w)

            full_text = " ".join(text_pieces)
            avg_conf = float(statistics.mean(confs)) if confs else 0.0
            return full_text, avg_conf, boxes

        notes: List[str] = []

        # Try several simple preprocessing strategies until we get text
        candidates = []

        # 1) If image has alpha, convert to RGB
        try:
            if img.mode in ("RGBA", "LA"):
                candidates.append(img.convert("RGB"))
            else:
                candidates.append(img.copy())
        except Exception:
            candidates.append(img.copy())

        # 2) Grayscale
        try:
            candidates.append(img.convert("L"))
        except Exception:
            pass

        # 3) Resize down if extremely large to speed up and improve OCR
        try:
            w, h = img.size
            max_dim = 2000
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                new_size = (int(w * scale), int(h * scale))
                candidates.append(img.resize(new_size))
        except Exception:
            pass

        # 4) Contrast enhancement and binarization variants
        try:
            from PIL import ImageEnhance
            enh = ImageEnhance.Contrast(img.convert("L"))
            candidates.append(enh.enhance(1.5))
            # simple binarization
            bw = img.convert("L").point(lambda p: 255 if p > 128 else 0)
            candidates.append(bw)
        except Exception:
            pass

        # Run through candidates
        for idx, cand in enumerate(candidates):
            try:
                txt, conf, boxes = run_tesseract(cand)
                if txt and txt.strip():
                    return {"text": txt, "confidence": conf, "bounding_boxes": boxes}
                else:
                    notes.append(f"candidate_{idx} produced no text (conf={conf})")
            except Exception:
                import traceback as _tb
                notes.append(f"candidate_{idx} exception: {_tb.format_exc()}")

        # If none produced text, return empty with diagnostic note
        return {"text": "", "confidence": 0.0, "bounding_boxes": [], "note": "; ".join(notes)}

    @staticmethod
    def _ocr_with_paddle(path: str) -> Dict[str, Any]:
        try:
            from paddleocr import PaddleOCR
            from PIL import Image
        except Exception as exc:
            raise RuntimeError("paddleocr or PIL not available") from exc

        ocr = PaddleOCR(use_angle_cls=True, lang="en")
        result = ocr.ocr(path, cls=True)
        text_pieces: List[str] = []
        boxes: List[List[int]] = []
        confs: List[float] = []
        for line in result:
            for seg in line:
                box = seg[0]
                txt = seg[1][0]
                score = seg[1][1]
                text_pieces.append(txt)
                confs.append(float(score))
                # Convert box to [x1,y1,x2,y2]
                xs = [int(pt[0]) for pt in box]
                ys = [int(pt[1]) for pt in box]
                boxes.append([min(xs), min(ys), max(xs), max(ys)])

        full_text = " ".join(text_pieces)
        avg_conf = float(statistics.mean(confs)) if confs else 0.0
        return {"text": full_text, "confidence": avg_conf, "bounding_boxes": boxes}

    @staticmethod
    def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
        # Validate input (raises jsonschema.ValidationError on mismatch)
        OCRExpert.validate_input(input_json)

        pages = input_json.get("pages", [1])
        page_files = input_json.get("page_files", [r"C:\Users\user\OneDrive\Belgeler\GitHub\OCRchestra\tests\sample_page.png"])

        ocr_results = []

        for idx, p in enumerate(pages):
            # Determine file path for this page if provided
            file_path = None
            if idx < len(page_files):
                candidate = page_files[idx]
                if os.path.exists(candidate):
                    file_path = candidate

            if file_path is None:
                # No file to run OCR on; return placeholder for this page
                ocr_results.append({
                    "page": p,
                    "text": "",
                    "confidence": 0.0,
                    "bounding_boxes": [],
                    "note": "No page file provided for OCR",
                })
                continue

            # Try pytesseract first, then paddleocr
            try:
                res = OCRExpert._ocr_with_pytesseract(file_path)
            except Exception as e_pyt:
                import traceback as _tb
                tb_pyt = _tb.format_exc()
                try:
                    res = OCRExpert._ocr_with_paddle(file_path)
                except Exception as e_pad:
                    tb_pad = _tb.format_exc()
                    # Include both tracebacks to help debugging
                    res = {
                        "text": "",
                        "confidence": 0.0,
                        "bounding_boxes": [],
                        "note": "pytesseract error:\n" + tb_pyt + "\nPaddleOCR error:\n" + tb_pad,
                    }

            entry = {"page": p, "text": res.get("text", ""), "confidence": res.get("confidence", 0.0), "bounding_boxes": res.get("bounding_boxes", [])}
            ocr_results.append(entry)

        result = {"document_id": input_json.get("document_id"), "pages": pages, "ocr": ocr_results}
        OCRExpert.validate_output(result)
        return result


def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
    return OCRExpert.execute(input_json)
