"""Minimal orchestrator skeleton for OCRchestra.

Responsibilities implemented here:
- Load a local HuggingFace model (tokenizer + model) from a provided local path.
- Accept document metadata as input (must NOT read document content).
- Generate a JSON execution plan using the local model.
- Validate that model output is strict JSON and conforms to a minimal schema.

Notes / Constraints:
- Models are loaded with `local_files_only=True` to avoid Hub/network calls.
- The orchestrator does not perform OCR or content reading.
- LLM is used only for planning; the code enforces JSON-only output.
- TODO: Add more robust prompt engineering, role separation, and auditing.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import jsonschema
import torch
from .model_loader import ModelLoader

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class Orchestrator:
    """Orchestrator that loads a local HF model and produces JSON execution plans.

    Usage:
        o = Orchestrator()
        o.load_model(model_path)
        plan = o.generate_plan(metadata)

    The `metadata` is a dict describing the document (IDs, source, page count, etc.).
    The orchestrator must NOT open or read the document's bytes/content.
    """

    def __init__(self, device: Optional[torch.device] = None):
        self.loader = ModelLoader(device=device)
        self.tokenizer = None
        self.model_path: Optional[str] = None
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))

    def load_model(self, model_path: str, **hf_kwargs) -> None:
        """Load model via `ModelLoader`.

        Accepts additional HuggingFace `from_pretrained` kwargs such as
        `device_map`, `load_in_8bit`, `trust_remote_code`, and `torch_dtype`.
        This enforces local-only loading unless overridden by explicit args.
        """
        self.model_path = model_path
        # Forward HF loader kwargs to ModelLoader (e.g., device_map, load_in_8bit)
        self.loader.load(model_path, **hf_kwargs)
        self.tokenizer = self.loader.tokenizer
        logger.info("Model loaded via ModelLoader from %s", model_path)

    def _build_prompt(self, metadata: Dict[str, Any]) -> str:
        # Minimal instruction: produce JSON matching execution plan schema, nothing else.
        instruction = (
            "You are an offline orchestrator assistant.\n"
            "Given the document metadata (no document content), produce a JSON object only.\n"
            "The JSON MUST conform to the minimal execution plan schema: {\n"
            "  \"version\": string,\n"
            "  \"plan\": array of step objects,\n"
            "  \"metadata\": the provided metadata\n"
            "}\n"
            "Return ONLY the JSON object and nothing else.\n"
        )

        prompt = {
            "instruction": instruction,
            "metadata": metadata,
        }

        # Use a compact JSON prompt to reduce chance of non-JSON output.
        return json.dumps(prompt, ensure_ascii=False)

    def generate_plan(self, metadata: Dict[str, Any], max_new_tokens: int = 256) -> Dict[str, Any]:
        """Generate an execution plan JSON using the loaded model.

        Returns a dict parsed from JSON produced by the model.

        Raises ValueError on validation/parsing errors.
        """
        if self.loader.model is None or self.loader.tokenizer is None:
            raise ValueError("Model not loaded. Call `load_model(model_path)` first.")

        prompt = self._build_prompt(metadata)

        # Use ModelLoader to generate deterministic text
        raw_text = self.loader.generate_text(prompt, max_new_tokens=max_new_tokens, temperature=0.0)

        # Extract JSON object from text (heuristic): find first '{' and last '}'
        try:
            start = raw_text.find("{")
            end = raw_text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw_text[start : end + 1]
            else:
                candidate = raw_text

            plan = json.loads(candidate)
        except Exception as exc:
            logger.exception("Failed to parse JSON from model output")
            raise ValueError("Model output is not valid JSON") from exc

        # Validate against minimal schema shipped with package
        schema_path = "ocrchestra/schemas/execution_plan_schema.json"
        try:
            with open(schema_path, "r", encoding="utf-8") as fh:
                schema = json.load(fh)
            jsonschema.validate(instance=plan, schema=schema)
        except Exception as exc:
            logger.exception("Execution plan failed schema validation")
            raise ValueError("Execution plan failed schema validation") from exc

        return plan

    def execute_pipeline(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a plan, route it, and execute stateless experts deterministically.

        Returns a dict containing the plan, routing decision, and expert outputs.
        """
        # Step 1: generate plan (LLM-driven, validated) unless a plan is provided
        if "plan" in metadata:
            provided = metadata.get("plan")
            # If user provided a plain list of steps, wrap into the expected
            # execution-plan dict so downstream code can use `plan.get("plan", [])`.
            if isinstance(provided, list):
                plan = {"version": "1.0", "plan": provided, "metadata": metadata}
            elif isinstance(provided, dict):
                plan = provided
            else:
                raise ValueError("Provided metadata 'plan' must be a list or dict")
        else:
            plan = self.generate_plan(metadata)

        # Step 2: routing
        try:
            from ocrchestra.experts import routing_expert
        except Exception:
            raise RuntimeError("Routing expert not available in environment")

        routing_input = {"document_id": metadata.get("document_id"), "plan": plan.get("plan", [])}
        route_result = routing_expert.execute(routing_input)

        # Step 3: execute experts in sequence
        expert_outputs = {}
        # Import known experts; keep imports local to avoid startup cost
        from ocrchestra.experts import ocr_expert, verifier_expert, post_correction_expert

        for expert_name in route_result.get("route", []):
            if expert_name == "ocr_expert":
                inp = {"document_id": metadata.get("document_id"), "pages": metadata.get("pages", [1]), "plan": plan.get("plan", [])}
                out = ocr_expert.execute(inp)
                expert_outputs.setdefault("ocr_expert", []).append(out)
            elif expert_name == "verifier_expert":
                inp = {"document_id": metadata.get("document_id"), "plan": plan.get("plan", [])}
                out = verifier_expert.execute(inp)
                expert_outputs.setdefault("verifier_expert", []).append(out)
            elif expert_name == "post_correction_expert":
                # Pass last OCR output if available
                last_ocr = expert_outputs.get("ocr_expert", [{}])[-1]
                out = post_correction_expert.execute(last_ocr)
                expert_outputs.setdefault("post_correction_expert", []).append(out)
            else:
                # Unknown expert: record as skipped
                expert_outputs.setdefault("unknown", []).append({"expert": expert_name, "status": "skipped"})

        return {"plan": plan, "route": route_result, "expert_outputs": expert_outputs}


if __name__ == "__main__":
    # Simple local dry-run example (will attempt to load model if path provided)
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="Local path to HF model folder")
    args = parser.parse_args()

    orch = Orchestrator()
    orch.load_model(args.model_path)
    sample_metadata = {"document_id": "example-0001", "pages": 1}
    try:
        plan = orch.generate_plan(sample_metadata)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error("Plan generation failed: %s", e)

    # Example: run the generated plan through routing and experts (if experts available)
    try:
        result = orch.execute_pipeline(sample_metadata)
        print("\nExecution result:\n", json.dumps(result, indent=2, ensure_ascii=False))
    except Exception:
        # ignore if experts not present; this is only a demo entrypoint
        pass
