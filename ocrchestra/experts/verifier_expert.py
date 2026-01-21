"""Verification expert stub.

Performs deterministic checks against a plan and returns a verification report.
"""
from __future__ import annotations

from typing import Dict, Any
from .base import ExpertBase


class VerifierExpert(ExpertBase):
    input_schema_path = "ocrchestra/schemas/expert_input_schema.json"
    output_schema_path = "ocrchestra/schemas/verifier_result_schema.json"

    @staticmethod
    def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
        VerifierExpert.validate_input(input_json)

        # Minimal deterministic verification: check presence of expected keys
        findings = []
        if "plan" not in input_json:
            findings.append({"severity": "critical", "message": "Missing plan field"})

        result = {
            "document_id": input_json.get("document_id"),
            "verified": len(findings) == 0,
            "findings": findings,
        }

        VerifierExpert.validate_output(result)
        return result


def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
    return VerifierExpert.execute(input_json)
