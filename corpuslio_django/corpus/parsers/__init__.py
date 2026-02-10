"""Corpus file parsers for VRT and CoNLL-U formats."""

from .conllu_parser import CoNLLUParser
from .vrt_parser import VRTParser

__all__ = ['CoNLLUParser', 'VRTParser']
