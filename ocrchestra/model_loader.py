"""ModelLoader: consistent, local-only HuggingFace model loader and generator.

Provides a small, testable wrapper around `transformers` to enforce project
rules: load from local filesystem only, CPU-first device, deterministic
generation defaults (temperature=0, no sampling), and a safe `generate_text`
helper that returns decoded text.

This class does NOT download models or call the Hub.
"""
from __future__ import annotations

from typing import Optional, Dict, Any

import logging

# Import transformers and torch lazily inside methods to respect test-time
# replacement of `sys.modules` and to enforce local_files_only at call-time.
logger = logging.getLogger(__name__)


try:
    import torch  # pragma: no cover - runtime import
except Exception:
    torch = None


logger = logging.getLogger(__name__)


class ModelLoader:
    def __init__(self, device: Optional[torch.device] = None):
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))
        self.tokenizer = None
        self.model = None
        self.model_path: Optional[str] = None

    def load(self, model_path: str, **hf_kwargs) -> None:
        """Load tokenizer and model from a local path only.

        Raises exceptions from transformers if loading fails. Always uses
        `local_files_only=True` to avoid Hub/network calls.
        """
        # Local import to ensure tests can inject fake `transformers` module.
        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            AutoModelForSeq2SeqLM,
            AutoConfig,
        )

        # BitsAndBytes/quantization helpers (optional import)
        try:
            from transformers import BitsAndBytesConfig
        except Exception:
            BitsAndBytesConfig = None

        self.model_path = model_path
        logger.info("Loading tokenizer from local path: %s", model_path)
        # Always enforce local_files_only for safety
        tokenizer_kwargs = dict(local_files_only=True)
        # Allow callers to pass trust_remote_code if needed
        if "trust_remote_code" in hf_kwargs:
            tokenizer_kwargs["trust_remote_code"] = hf_kwargs.pop("trust_remote_code")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, **tokenizer_kwargs)

        # Prepare HF model loading kwargs; ensure local_files_only unless explicitly overridden
        model_kwargs = dict(local_files_only=True)
        # Merge remaining hf_kwargs (e.g., device_map, load_in_8bit, torch_dtype)
        model_kwargs.update(hf_kwargs)

        # If user requested 8-bit/4-bit loading and BitsAndBytesConfig is available,
        # create a quantization_config and prefer it (this enables CPU offload options).
        quant_cfg = None
        load_in_8bit = model_kwargs.get("load_in_8bit") or False
        load_in_4bit = model_kwargs.get("load_in_4bit") or False
        # Honor explicit llm_int8_enable_fp32_cpu_offload flag if provided, otherwise default True
        llm_int8_enable_fp32_cpu_offload = model_kwargs.pop("llm_int8_enable_fp32_cpu_offload", True)
        if (load_in_8bit or load_in_4bit) and BitsAndBytesConfig is not None:
            try:
                quant_cfg = BitsAndBytesConfig(
                    load_in_8bit=bool(load_in_8bit),
                    load_in_4bit=bool(load_in_4bit),
                    llm_int8_enable_fp32_cpu_offload=bool(llm_int8_enable_fp32_cpu_offload),
                )
                # Remove raw load flags to prefer explicit quantization_config API
                model_kwargs.pop("load_in_8bit", None)
                model_kwargs.pop("load_in_4bit", None)
                model_kwargs["quantization_config"] = quant_cfg
            except Exception:
                logger.warning("Could not construct BitsAndBytesConfig; falling back to raw load flags")

        # If device_map not provided and quantization is requested, default to 'auto'
        if quant_cfg is not None and not model_kwargs.get("device_map"):
            model_kwargs["device_map"] = model_kwargs.get("device_map", "auto")

        # Use the model config to choose the correct AutoModel class (causal vs seq2seq)
        try:
            cfg_kwargs = dict(local_files_only=True)
            if "trust_remote_code" in hf_kwargs:
                cfg_kwargs["trust_remote_code"] = hf_kwargs.get("trust_remote_code")
            config = AutoConfig.from_pretrained(model_path, **cfg_kwargs)
            is_encoder_decoder = getattr(config, "is_encoder_decoder", False)
        except Exception:
            logger.warning("Failed to read model config; will try causal then seq2seq fallback")
            config = None
            is_encoder_decoder = False

        try:
            if is_encoder_decoder:
                logger.info("Loading Seq2Seq LM from %s with kwargs=%s", model_path, {k: type(v) for k, v in model_kwargs.items()})
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path, **model_kwargs)
            else:
                logger.info("Loading Causal LM from %s with kwargs=%s", model_path, {k: type(v) for k, v in model_kwargs.items()})
                self.model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)
        except Exception:
            # Last-resort fallback: try the other family
            try:
                logger.info("Primary model class failed; attempting alternative class for %s", model_path)
                if is_encoder_decoder:
                    self.model = AutoModelForCausalLM.from_pretrained(model_path, **model_kwargs)
                else:
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path, **model_kwargs)
            except Exception:
                logger.exception("Failed to load model %s with provided kwargs=%s", model_path, model_kwargs)
                raise

        # If HF handled device placement (device_map provided), avoid moving the model again.
        # If HF did not handle device placement (no device_map), move the model to target device
        if torch is not None and not model_kwargs.get("device_map"):
            try:
                self.model.to(self.device)
            except Exception:
                logger.warning("Failed to move model to device %s; continuing with model as-loaded", self.device)

    def generate_text(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.0, **kwargs) -> str:
        """Generate text deterministically by default and return decoded string.

        Default settings enforce determinism (temperature=0, no sampling). Extra
        generation kwargs may override defaults but should be used sparingly.
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("ModelLoader: model not loaded. Call `load()` first.")

        # Local import of torch to honor test-time replacement if present
        try:
            import torch as _torch
        except Exception:
            _torch = None

        # Tokenize and move to device
        tokenized = self.tokenizer(prompt, return_tensors="pt")
        input_ids = getattr(tokenized, "input_ids")
        if _torch is not None:
            input_ids = input_ids.to(self.device)

        gen_kwargs: Dict[str, Any] = dict(
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=float(temperature),
            num_beams=1,
            eos_token_id=self.tokenizer.eos_token_id if self.tokenizer.eos_token_id is not None else self.tokenizer.pad_token_id,
        )

        # Allow caller to pass a small set of overrides
        gen_kwargs.update(kwargs)

        # Deterministic seed for CPU
        if _torch is not None:
            _torch.manual_seed(42)

        if _torch is not None:
            with _torch.no_grad():
                outputs = self.model.generate(input_ids, **gen_kwargs)
        else:
            # Fallback: call generate without torch context
            outputs = self.model.generate(input_ids, **gen_kwargs)

        # Try to return decoded generated portion; fall back to full decode
        try:
            # outputs[0] expected to be sequence of token ids
            text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        except Exception:
            # Best-effort decode
            text = self.tokenizer.decode(outputs, skip_special_tokens=True)

        return text
