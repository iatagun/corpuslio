"""Simple Turkish fuzzy fallback for OCR post-correction.

This module provides a lightweight, dependency-free fuzzy corrector using
Python's stdlib `difflib.get_close_matches`. It ships with a small built-in
Turkish wordlist that can be extended via `domain_lexicon` passed at runtime.

The goal is a fast, offline fallback when the LLM fails to produce a useful
correction.
"""
from __future__ import annotations

from typing import Iterable, List, Tuple, Optional, Set
import re
from difflib import get_close_matches


def _default_wordlist() -> Set[str]:
    # Small curated Turkish wordlist to cover common elementary reading text.
    words = [
        "yağız", "öğlen", "okuldan", "eve", "geldi", "çantasını", "koltuğun",
        "üzerine", "bıraktı", "oyuncağını", "alıp", "oynamaya", "başladı",
        "annesi", "daha", "dikkatli", "oynaması", "için", "uyardı",
        "dinleyerek", "oynadı", "oyun", "bittikten", "sonra", "oyuncaklarını",
        "güzelce", "topladı", "yağız'", "yağız", "çanta", "koltuk",
        "nereden", "nereye", "neden", "ne yaptı", "oyun", "bittiğinde",
        "metin", "soru", "cevap", "okul", "ev", "başlamak", "bırakmak",
    ]
    return set(words)


_WORDLIST = _default_wordlist()


def simple_tokenize(text: str) -> List[str]:
    # Split into word-like tokens
    return re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", text, flags=re.UNICODE)


def fuzzy_correct_text(text: str, domain_lexicon: Optional[Iterable[str]] = None, max_suggestions: int = 1, cutoff: float = 0.7) -> Tuple[str, List[Tuple[str, str]]]:
    """Return corrected text and list of (original, corrected) replacements.

    - domain_lexicon: additional preferred spellings (list of words)
    - cutoff: similarity cutoff for difflib.get_close_matches
    """
    domain = set(w.lower() for w in domain_lexicon) if domain_lexicon else set()
    candidates = list(_WORDLIST | domain)

    # Tokenize into words and non-words to reconstruct
    parts = re.split(r"(\W+)", text, flags=re.UNICODE)
    corrections: List[Tuple[str, str]] = []
    out_parts: List[str] = []
    for part in parts:
        if not part:
            continue
        if re.match(r"^\W+$", part, flags=re.UNICODE):
            out_parts.append(part)
            continue
        # word-like token
        lower = part.lower()
        if lower in domain or lower in _WORDLIST:
            out_parts.append(part)
            continue
        # try close matches
        matches = get_close_matches(lower, candidates, n=max_suggestions, cutoff=cutoff)
        if matches:
            best = matches[0]
            # preserve capitalization form
            if part.istitle():
                repl = best.capitalize()
            elif part.isupper():
                repl = best.upper()
            else:
                repl = best
            out_parts.append(repl)
            corrections.append((part, repl))
        else:
            out_parts.append(part)

    corrected = "".join(out_parts)
    return corrected, corrections
