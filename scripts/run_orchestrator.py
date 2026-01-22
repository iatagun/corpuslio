"""Small CLI to demonstrate orchestrator usage without reading document content.

This script intentionally avoids any network activity and assumes a local model path.
"""
import json
import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path so `ocrchestra` package can be imported
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ocrchestra.orchestrator import Orchestrator


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-path", required=True, help="Local HuggingFace model folder path")
    p.add_argument("--metadata-file", help="Path to a JSON file containing document metadata")
    p.add_argument("--device", choices=["cpu", "cuda", "auto"], default="auto", help="Preferred device placement")
    p.add_argument("--load-in-8bit", action="store_true", help="Attempt to load model in 8-bit (requires bitsandbytes)")
    p.add_argument("--trust-remote-code", action="store_true", help="Pass trust_remote_code to HF loader if necessary (use only for trusted models)")
    p.add_argument("--device-map", help="Explicit device_map to pass to HF loader (e.g., 'auto' or JSON mapping)")
    args = p.parse_args()

    if args.metadata_file:
        metadata = json.loads(Path(args.metadata_file).read_text(encoding="utf-8"))
    else:
        metadata = {"document_id": "sample-0001", "source": "unknown", "pages": 1}

    orch = Orchestrator()
    hf_kwargs = {}
    if args.load_in_8bit:
        hf_kwargs["load_in_8bit"] = True
    if args.trust_remote_code:
        hf_kwargs["trust_remote_code"] = True
    if args.device_map:
        # allow explicit device_map string like 'auto'
        hf_kwargs["device_map"] = args.device_map
    else:
        if args.device == "cpu":
            hf_kwargs["device_map"] = None
        else:
            hf_kwargs["device_map"] = "auto"

    # If the user provided a metadata file that already contains a plan, skip
    # loading the (potentially large) model; execute_pipeline will use the
    # provided plan. Otherwise, load the model from disk.
    skip_model_load = False
    if args.metadata_file:
        try:
            m = json.loads(Path(args.metadata_file).read_text(encoding="utf-8"))
            if isinstance(m, dict) and "plan" in m:
                skip_model_load = True
                metadata = m
        except Exception:
            # ignore and fall back to normal behavior
            pass

    if not skip_model_load:
        orch.load_model(args.model_path, **hf_kwargs)
    result = orch.execute_pipeline(metadata)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
