"""Unit tests for `ocrchestra.orchestrator` using mocked transformers/torch.

These tests inject lightweight fake `transformers` and `torch` modules
into `sys.modules` before importing the orchestrator so tests run
without heavy dependencies.
"""
import importlib
import sys
import types
import json


def make_fake_torch_module():
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

    # minimal no_grad context manager
    class _NoGrad:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    mod.no_grad = lambda: _NoGrad()

    # minimal backends/cudnn stub
    backends = types.SimpleNamespace()
    backends.cudnn = types.SimpleNamespace(deterministic=False, benchmark=True)
    mod.backends = backends

    return mod


def make_fake_transformers_module(json_response: dict):
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
                    self.input_ids = self

                def to(self, device):
                    return self

            return Input()

        def decode(self, token_ids, skip_special_tokens=True):
            # Return compact JSON; orchestrator will attempt to find '{'
            return json.dumps(json_response, ensure_ascii=False)

    class FakeModel:
        @classmethod
        def from_pretrained(cls, path, local_files_only=True):
            return cls()

        def to(self, device):
            return self

        def generate(self, input_ids, **kwargs):
            # Return a placeholder; tokenizer.decode ignores the arg
            return [None]

    mod.AutoTokenizer = FakeTokenizer
    mod.AutoModelForCausalLM = FakeModel
    mod.AutoModelForSeq2SeqLM = FakeModel

    return mod


def test_orchestrator_generates_valid_plan(tmp_path, monkeypatch):
    # Build a fake expected plan that conforms to schema
    expected_plan = {
        "version": "1.0",
        "plan": [
            {"step_id": "s1", "action": "ocr.detect", "parameters": {"pages": [1]}},
        ],
        "metadata": {"document_id": "fake-1"},
    }

    # Inject fake torch and transformers modules before importing orchestrator
    sys.modules["torch"] = make_fake_torch_module()
    sys.modules["transformers"] = make_fake_transformers_module(expected_plan)

    # Ensure repository root is on sys.path so `ocrchestra` package can be imported
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(repo_root))

    # Now import the orchestrator module fresh
    orch_mod = importlib.import_module("ocrchestra.orchestrator")
    importlib.reload(orch_mod)

    Orchestrator = orch_mod.Orchestrator

    orch = Orchestrator()

    # Loading model should use the fake from_pretrained implementations
    orch.load_model(str(tmp_path))

    # Generate a plan
    metadata = {"document_id": "fake-1"}
    plan = orch.generate_plan(metadata)

    assert isinstance(plan, dict)
    assert plan["version"] == expected_plan["version"]
    assert plan["metadata"]["document_id"] == "fake-1"
    assert isinstance(plan["plan"], list)
