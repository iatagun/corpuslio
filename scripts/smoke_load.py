"""Smoke-test loader for a local HuggingFace model using the project's ModelLoader.

Usage:
  python scripts/smoke_load.py --model-path models/qwen2.5-3b-instruct

This script only attempts to load the tokenizer and model (no generation),
and prints simple diagnostics. It inserts the project root on `sys.path`
so it can be used from the repository root.
"""
import sys
from pathlib import Path
import argparse
import traceback

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from corpuslio.model_loader import ModelLoader


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-path", required=True, help="Local model directory")
    p.add_argument("--device", choices=["cpu", "cuda", "auto"], default="auto", help="Preferred device placement (auto chooses cuda if available)")
    p.add_argument("--load-in-8bit", action="store_true", help="Attempt to load model in 8-bit (requires bitsandbytes)")
    p.add_argument("--trust-remote-code", action="store_true", help="Pass trust_remote_code to HF loader if necessary (use only for trusted models)")
    args = p.parse_args()

    loader = ModelLoader()
    try:
        print("Loading model from:", args.model_path)
        hf_kwargs = {}
        if args.load_in_8bit:
            hf_kwargs["load_in_8bit"] = True
        # Map device flag to HF device_map behavior
        if args.device == "cpu":
            hf_kwargs["device_map"] = None
        elif args.device == "cuda":
            # Let HF place on CUDA; require a single GPU or device_map support
            hf_kwargs["device_map"] = "auto"
        else:
            # auto: attempt to let HF choose an optimal device map if available
            hf_kwargs["device_map"] = "auto"
        if args.trust_remote_code:
            hf_kwargs["trust_remote_code"] = True

        loader.load(args.model_path, **hf_kwargs)
        print("Model loaded successfully.")
        print("Tokenizer:", type(loader.tokenizer))
        print("Model:", type(loader.model))
        # Print a small tokenization sanity check
        sample = "Hello"
        tokens = loader.tokenizer(sample)
        print("Sample token length:", len(tokens.get("input_ids", [])))
    except Exception as exc:
        print("Model load failed:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
