"""Integration-style unit test for the orchestrator pipeline.

Mocks the HF model output to produce a known plan and verifies that the
orchestrator routes and executes expert stubs deterministically.
"""
import importlib
import sys
from pathlib import Path


def make_fake_torch_module():
    import types

    mod = types.ModuleType("torch")

    class Device:
        def __init__(self, name):
            self.name = name

        def __str__(self):
            return self.name

    mod.device = Device

    class Cuda:
        @staticmethod
        def is_available():
            return False

    mod.cuda = Cuda()

    def manual_seed(seed):
        return None

    mod.manual_seed = manual_seed

    # minimal backends/cudnn stub
    backends = types.SimpleNamespace()
    backends.cudnn = types.SimpleNamespace(deterministic=False, benchmark=True)
    mod.backends = backends

    class _NoGrad:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    mod.no_grad = lambda: _NoGrad()

    return mod


def make_fake_transformers_module(json_response: dict):
    import types
    import json

    mod = types.ModuleType("transformers")

    class FakeTokenizer:
        def __init__(self):
            self.eos_token_id = None
            self.pad_token_id = 0

        @classmethod
        def from_pretrained(cls, path, local_files_only=True):
            return cls()

        def __call__(self, prompt, return_tensors=None):
            class Input:
                def __init__(self):
                    # shape should mimic (batch, seq)
                    self.shape = (1, 1)
                    self.input_ids = self

                def to(self, device):
                    return self

            return Input()

        def decode(self, token_ids, skip_special_tokens=True):
            return json.dumps(json_response, ensure_ascii=False)

    class FakeModel:
        @classmethod
        def from_pretrained(cls, path, local_files_only=True):
            return cls()

        def to(self, device):
            return self

        def generate(self, input_ids, **kwargs):
            return [[0, 1, 2]]

    mod.AutoTokenizer = FakeTokenizer
    mod.AutoModelForCausalLM = FakeModel
    mod.AutoModelForSeq2SeqLM = FakeModel

    return mod


def test_orchestrator_pipeline_runs(tmp_path):
    # Plan includes an OCR step and a verification step
    expected_plan = {
        "version": "1.0",
        "plan": [
            {"step_id": "s1", "action": "ocr.detect", "parameters": {}},
            {"step_id": "s2", "action": "verify.plan", "parameters": {}},
        ],
        "metadata": {"document_id": "doc-pipeline"},
    }

    # Inject fakes
    sys.modules["torch"] = make_fake_torch_module()
    sys.modules["transformers"] = make_fake_transformers_module(expected_plan)

    # Ensure package import works
    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    orch_mod = importlib.import_module("ocrchestra.orchestrator")
    importlib.reload(orch_mod)

    Orchestrator = orch_mod.Orchestrator
    orch = Orchestrator()
    orch.load_model(str(tmp_path))

    metadata = {"document_id": "doc-pipeline", "pages": [1]}
    result = orch.execute_pipeline(metadata)

    assert "plan" in result
    assert "route" in result
    assert "expert_outputs" in result
    # OCR expert should have been called
    assert "ocr_expert" in result["expert_outputs"]
