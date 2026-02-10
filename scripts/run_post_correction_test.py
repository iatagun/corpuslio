"""Run a post-correction expert test (PowerShell-friendly).

Usage:
  python scripts/run_post_correction_test.py --model-path models\qwen2.5-3b-instruct

This script calls `post_correction_expert` with a sample OCR result and prints JSON.
"""
import sys
from pathlib import Path
import argparse
import json

# Ensure repo root on sys.path when invoked from workspace root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from corpuslio.experts import post_correction_expert


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-path", help="Local HF model path for post-correction", default=None)
    p.add_argument("--load-in-8bit", action="store_true", help="Attempt to load model in 8-bit (requires bitsandbytes)")
    p.add_argument("--device-map", help="Device map to pass to HF loader (e.g., 'auto' or 'None')", default=None)
    p.add_argument("--llm-int8-enable-fp32-offload", action="store_true", help="Set llm_int8_enable_fp32_cpu_offload=True for bnb")
    p.add_argument("--trust-remote-code", action="store_true", help="Pass trust_remote_code=True to tokenizer/model loader if required by the repo")
    p.add_argument("--num-beams", type=int, help="num_beams for generation", default=None)
    p.add_argument("--max-new-tokens", type=int, help="max_new_tokens for generation", default=None)
    p.add_argument("--debug", action="store_true", help="Include raw model output in JSON result for debugging")
    args = p.parse_args()

    # Sample OCR output (use your real OCR output or modify as needed)
    sample_ocr = {
        "document_id": "test-ocr",
        "ocr": [
            {
                "page": 1,
                "text": "i = Hr ~ tor rome. see het Bi Ss a enw",
                "confidence": 0.21916666666666668,
                "bounding_boxes": []
            }
        ]
    }

    if args.model_path:
        sample_ocr["model_path"] = args.model_path
        model_kwargs = {}
        if args.load_in_8bit:
            model_kwargs["load_in_8bit"] = True
        if args.device_map:
            # interpret string 'None' as None
            model_kwargs["device_map"] = None if args.device_map.lower() == "none" else args.device_map
        if args.llm_int8_enable_fp32_offload:
            model_kwargs["llm_int8_enable_fp32_cpu_offload"] = True
        if args.trust_remote_code:
            model_kwargs["trust_remote_code"] = True
        if model_kwargs:
            sample_ocr["model_kwargs"] = model_kwargs
        # Generation tuning options
        gen_kwargs = {}
        if args.num_beams:
            gen_kwargs["num_beams"] = args.num_beams
        if args.max_new_tokens:
            gen_kwargs["max_new_tokens"] = args.max_new_tokens
        if gen_kwargs:
            sample_ocr["generation_kwargs"] = gen_kwargs
        if args.debug:
            sample_ocr["debug"] = True

    res = post_correction_expert.execute(sample_ocr)
    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
