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
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
)

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
        self.model = None
        self.tokenizer = None
        self.model_path: Optional[str] = None
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))

    def load_model(self, model_path: str) -> None:
        """Load tokenizer and model from a local path.

        model_path: Local filesystem path where the model files exist.

        This method uses `local_files_only=True` to ensure no network calls.
        It attempts to load a causal LM first, then a seq2seq LM.
        """
        self.model_path = model_path
        logger.info("Loading tokenizer from %s (local_files_only=True)", model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)

        # Try causal LM first, then seq2seq. Do not attempt downloads.
        try:
            logger.info("Attempting to load causal LM model from %s", model_path)
            self.model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True)
        except Exception:
            logger.info("Causal LM load failed; attempting to load seq2seq model from %s", model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path, local_files_only=True)

        # Move to device (CPU-first; GPU optional)
        self.model.to(self.device)
        # Make deterministic where possible
        if torch.cuda.is_available():
            try:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
            except Exception:
                pass

        logger.info("Model loaded and moved to %s", self.device)

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
        if self.model is None or self.tokenizer is None:
            raise ValueError("Model not loaded. Call `load_model(model_path)` first.")

        prompt = self._build_prompt(metadata)

        input_ids = self.tokenizer(prompt, return_tensors="pt").input_ids.to(self.device)

        # Deterministic generation: no sampling, temperature=0
        gen_kwargs = dict(
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=0.0,
            num_beams=1,
            eos_token_id=self.tokenizer.eos_token_id if self.tokenizer.eos_token_id is not None else self.tokenizer.pad_token_id,
        )

        # Set a seed for repeatability on CPU
        torch.manual_seed(42)

        with torch.no_grad():
            outputs = self.model.generate(input_ids, **gen_kwargs)

        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # The prompt itself may be included in the decoded text for some models; try to extract trailing JSON.
        # Heuristic: find the first '{' after the prompt content.
        try:
            # If the model repeats the prompt, we attempt to find the JSON object in the generated text
            json_start = text.find("{")
            if json_start != -1:
                candidate = text[json_start:]
            else:
                candidate = text

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
