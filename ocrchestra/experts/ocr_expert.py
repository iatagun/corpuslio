"""OCR expert stub (stateless).

This expert does NOT perform OCR; it returns a deterministic, schema-conformant
placeholder result so the orchestrator and integration tests can be exercised.
"""
from __future__ import annotations

from typing import Dict, Any
from .base import ExpertBase


class OCRExpert(ExpertBase):
    input_schema_path = "ocrchestra/schemas/expert_input_schema.json"
    output_schema_path = "ocrchestra/schemas/ocr_result_schema.json"

    @staticmethod
    def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
        # Validate input (raises jsonschema.ValidationError on mismatch)
        OCRExpert.validate_input(input_json)

        # Stateless placeholder response
        result = {
            "document_id": input_json.get("document_id"),
            "pages": input_json.get("pages", []),
            "ocr": [
                {
                    "page": p,
                    "text": "",
                    "confidence": 0.0,
                    "bounding_boxes": [],
                    "note": "TODO: implement OCR. This is a placeholder.",
                }
                for p in input_json.get("pages", [1])
            ],
        }

        OCRExpert.validate_output(result)
        return result


def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
    return OCRExpert.execute(input_json)
