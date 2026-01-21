# OCRchestra

OCRchestra is a modular, production-grade OCR orchestration system focused on
evidence-based OCR, deterministic processing, and strict separation of
responsibilities between an orchestrator and expert modules.

**Core constraints**
- All language models are loaded from local filesystem paths (HuggingFace format).
- No network calls, no Hub downloads, and no remote inference APIs.
- LLMs are used only for planning, routing, verification, and post-correction.
- OCR extraction is evidence-based (confidence scores, bounding boxes).

**Principles**
- Deterministic behavior where possible.
- JSON contracts between modules; expert modules are stateless and isolated.
- Models loaded with `local_files_only=True` (transformers).

**Quick Start**

Prerequisites
- Python 3.8+ (3.11 recommended)
- A local HuggingFace-format model folder available on disk (do NOT rely on downloads)
- Install dev/runtime dependencies (offline install if required):

```bash
pip install -r requirements.txt
```

Run the orchestrator (example):

```bash
python scripts/run_orchestrator.py --model-path "C:\path\to\local\hf-model"
```

Pass a metadata file (JSON) to `--metadata-file` to provide document metadata.

**Testing**

Unit tests use lightweight mocks for `torch` and `transformers` so they do not
require heavy model files. Run tests with:

```bash
pytest -q
```

Real OCR expert
- The repository includes a real OCR expert (`ocr_expert_real`) that uses the
	Tesseract binary via `pytesseract` and `Pillow` to extract text, bounding
	boxes, and per-word confidence scores.
- Requirements: install system Tesseract (e.g., `apt install tesseract-ocr` on
	Debian/Ubuntu, or download installer for Windows) and Python packages from
	`requirements.txt`.
- The OCR unit test is skipped when Tesseract or `pytesseract` is not available.


**Repository layout**
- `ocrchestra/orchestrator.py` — orchestrator skeleton, model loader, JSON-only plan generation
- `ocrchestra/schemas/execution_plan_schema.json` — minimal execution plan JSON Schema
- `scripts/run_orchestrator.py` — small CLI demonstrating orchestrator usage
- `tests/test_orchestrator.py` — pytest unit tests (mocks HF and torch)
- `requirements.txt` — minimal runtime and test dependencies

Security & audit notes
- The orchestrator intentionally does not read or modify document content.
- TODO: add logging, signing of plans, and audit trails for production use.

Contributing
- Follow the modular contract: orchestrator emits JSON plans; experts accept JSON.
- Add TODOs and tests when extending behavior.
