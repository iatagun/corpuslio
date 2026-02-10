"""Run a quick OCR expert test (Windows-friendly).

Usage:
  python scripts/run_ocr_test.py

This script calls the `ocr_expert` with `tests/sample_page.png` and prints JSON.
"""
from pathlib import Path
import json

# Ensure repo root on path when invoked from workspace root
import sys
from pathlib import Path as _P
ROOT = _P(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from corpuslio.experts import ocr_expert


def main():
    sample = Path("tests/sample_page.png")
    if not sample.exists():
        print("Sample page not found:", sample)
        raise SystemExit(1)

    inp = {"document_id": "test-ocr", "pages": [1], "page_files": [str(sample)]}
    res = ocr_expert.execute(inp)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
