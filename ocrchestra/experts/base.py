"""Base class and helpers for expert modules.

Experts are stateless: implement `execute(input_json: dict) -> dict`.
This module provides a small helper for schema validation.
"""
from __future__ import annotations

import json
from typing import Dict, Any

import jsonschema


class ExpertBase:
    input_schema_path: str | None = None
    output_schema_path: str | None = None

    @classmethod
    def _load_schema(cls, path: str) -> Dict[str, Any]:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    @classmethod
    def validate_input(cls, data: Dict[str, Any]) -> None:
        if cls.input_schema_path:
            schema = cls._load_schema(cls.input_schema_path)
            jsonschema.validate(instance=data, schema=schema)

    @classmethod
    def validate_output(cls, data: Dict[str, Any]) -> None:
        if cls.output_schema_path:
            schema = cls._load_schema(cls.output_schema_path)
            jsonschema.validate(instance=data, schema=schema)
