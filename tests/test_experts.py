"""Unit tests for expert module skeletons.

These tests verify that each expert accepts JSON input and returns schema-
conformant JSON output. They are deterministic and do not rely on models.
"""
import json
from pathlib import Path
import sys

import jsonschema

# Ensure repository root is on sys.path so local package imports work during tests
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from ocrchestra.experts import ocr_expert, verifier_expert, post_correction_expert, routing_expert


def test_ocr_expert_returns_schema_conformant_result(tmp_path):
    inp = {"document_id": "doc-1", "pages": [1, 2]}
    res = ocr_expert.execute(inp)
    # Validate against schema
    schema = json.loads(Path("ocrchestra/schemas/ocr_result_schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=res, schema=schema)


def test_verifier_expert_detects_missing_plan():
    inp = {"document_id": "doc-2"}
    res = verifier_expert.execute(inp)
    schema = json.loads(Path("ocrchestra/schemas/verifier_result_schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=res, schema=schema)
    assert res["verified"] is False


def test_post_correction_returns_structure():
    ocr_result = {"document_id": "doc-3", "ocr": [{"page": 1, "text": "", "confidence": 0.0, "bounding_boxes": []}]}
    res = post_correction_expert.execute(ocr_result)
    schema = json.loads(Path("ocrchestra/schemas/post_correction_schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(instance=res, schema=schema)


def test_routing_expert_routes_correctly():
    plan = {"document_id": "doc-4", "plan": [{"step_id": "s1", "action": "ocr.detect"}, {"step_id": "s2", "action": "verify.plan"}]}
    res = routing_expert.execute(plan)
    assert res["route"] == ["ocr_expert", "verifier_expert"]
