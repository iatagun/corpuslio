"""Small CLI to demonstrate orchestrator usage without reading document content.

This script intentionally avoids any network activity and assumes a local model path.
"""
import json
import argparse
from pathlib import Path

from ocrchestra.orchestrator import Orchestrator


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-path", required=True, help="Local HuggingFace model folder path")
    p.add_argument("--metadata-file", help="Path to a JSON file containing document metadata")
    args = p.parse_args()

    if args.metadata_file:
        metadata = json.loads(Path(args.metadata_file).read_text(encoding="utf-8"))
    else:
        metadata = {"document_id": "sample-0001", "source": "unknown", "pages": 1}

    orch = Orchestrator()
    orch.load_model(args.model_path)
    plan = orch.generate_plan(metadata)
    print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
