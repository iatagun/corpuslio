"""
Parsers for various corpus formats.

Available parsers:
- CoNLLUParser: Parse and serialize CoNLL-U format dependency annotations
"""

from .conllu_parser import CoNLLUParser

__all__ = ['CoNLLUParser']
