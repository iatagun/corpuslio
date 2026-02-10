"""Routing expert stub.

Determines which experts should run next based on an execution plan. This is
deterministic and does not call external models.
"""
from __future__ import annotations

from typing import Dict, Any, List


def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
    # Very small deterministic router: look for actions in plan and map to experts
    route: List[str] = []
    plan = input_json.get("plan", [])
    for step in plan:
        action = step.get("action", "")
        if action.startswith("ocr."):
            route.append("ocr_expert")
        elif action.startswith("verify."):
            route.append("verifier_expert")
        elif action.startswith("post_correction."):
            route.append("post_correction_expert")

    return {"document_id": input_json.get("document_id"), "route": route}
