"""LLM-backed Post-Correction Expert.

This expert accepts OCR results and uses a local HuggingFace model (via
`ModelLoader`) to perform conservative corrections. Rules enforced by the
prompt:
- DO NOT add new words.
- ONLY correct obvious OCR errors.
- If uncertain about a correction, wrap the uncertain fragment with
  [[UNCERTAIN]] ... [[/UNCERTAIN]].

The model path may be provided via `input_json["model_path"]` or the
environment variable `POST_CORRECT_MODEL_PATH`. If no model is available,
the expert returns the original OCR text with a note.
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional
from .base import ExpertBase
import os
import traceback

from ..model_loader import ModelLoader
from ..ocr_fallback import fuzzy_correct_text


class PostCorrectionExpert(ExpertBase):
    input_schema_path = "ocrchestra/schemas/ocr_result_schema.json"
    output_schema_path = "ocrchestra/schemas/post_correction_schema.json"

    # simple cached loader to avoid reloading model on each call
    _loader: Optional[ModelLoader] = None
    _loaded_model_path: Optional[str] = None

    @classmethod
    def _ensure_model(cls, model_path: str, hf_kwargs: Optional[Dict[str, Any]] = None) -> None:
        hf_kwargs = hf_kwargs or {}
        if cls._loader is None or cls._loaded_model_path != model_path:
            cls._loader = ModelLoader()
            cls._loader.load(model_path, **hf_kwargs)
            cls._loaded_model_path = model_path

    @staticmethod
    def _build_prompt(ocr_text: str, domain_lexicon: Optional[List[str]] = None) -> str:
        rules = (
            "OCR Sonrası Düzeltme Asistanısınız.\n"
            "Verilen OCR metni için İKİ farklı düzeltme üretin:\n"
            "1) MUHAFAZAKÂR (CONSERVATIVE): Yalnızca belirgin OCR karakter hatalarını düzeltin, yeni kelime veya içerik EKLEMEYİN.\n"
            "2) AGRESİF (AGGRESSIVE): Kırık, eksik veya bozulmuş kelimeleri tahmin ederek metni en iyi şekilde onarmaya çalışın — bu seçenekte GEREKİRSE kelimeler ekleyebilirsiniz.\n"
            "Belirsiz bir düzeltme yapıyorsanız o parçayı [[UNCERTAIN]]...[[/UNCERTAIN]] ile işaretleyin.\n"
            "Çıktı: Sadece iki düzeltme varyantını, aşağıdaki açık işaretler (marker) arasına koyarak ve başka hiçbir şey eklemeden döndürün.\n"
            "Aşağıdaki biçimi SAKLAYIN (işaretleri aynen kullanın):\n"
            "===CONSERVATIVE===<conservative text>===END_CONSERVATIVE===\n"
            "===AGGRESSIVE===<aggressive text>===END_AGGRESSIVE===\n"
        )

        lex = ""
        if domain_lexicon:
            lex = "\nDomain lexicon (prefer these spellings):\n" + ", ".join(domain_lexicon)

        prompt = (
            f"{rules}{lex}\nOrijinal OCR metni:\n'''{ocr_text}'''\n\n"
            "Lütfen yukarıdaki işaret formatını kullanarak sadece belirtilen markerlar arasına düzeltmeleri yazın; ekstra açıklama veya tekrar ETMEYİN.\n"
        )
        return prompt

    @classmethod
    def execute(cls, input_json: Dict[str, Any]) -> Dict[str, Any]:
        PostCorrectionExpert.validate_input(input_json)

        # Determine model path
        model_path = input_json.get("model_path") or os.environ.get("POST_CORRECT_MODEL_PATH")
        hf_kwargs = input_json.get("model_kwargs", {}) or {}

        corrections: List[Dict[str, Any]] = []

        # If no model available, return original OCR text with a note
        if not model_path:
            for page_entry in input_json.get("ocr", []):
                corrections.append({
                    "page": page_entry.get("page"),
                    "corrected_text": page_entry.get("text", ""),
                })
            result = {"document_id": input_json.get("document_id"), "post_corrections": corrections, "note": "No post-correction model configured."}
            PostCorrectionExpert.validate_output(result)
            return result

        # Ensure model is loaded (may raise if loading fails)
        try:
            cls._ensure_model(model_path, hf_kwargs=hf_kwargs)
        except Exception:
            tb = traceback.format_exc()
            # Fall back: return original text with error note
            for page_entry in input_json.get("ocr", []):
                corrections.append({"page": page_entry.get("page"), "corrected_text": page_entry.get("text", "")})
            result = {"document_id": input_json.get("document_id"), "post_corrections": corrections, "note": "Model load failed: " + tb}
            PostCorrectionExpert.validate_output(result)
            return result

        # For each OCR page, ask the model to correct conservatively
        for page_entry in input_json.get("ocr", []):
            page = page_entry.get("page")
            text = page_entry.get("text", "")
            domain = input_json.get("domain_lexicon")

            prompt = cls._build_prompt(text, domain_lexicon=domain)

            try:
                # Allow caller to pass generation overrides (useful for tuning)
                gen_overrides = input_json.get("generation_kwargs", {}) or {}
                # Default conservative but stronger search settings
                default_num_beams = gen_overrides.get("num_beams", 8)
                default_max_new_tokens = gen_overrides.get("max_new_tokens", max(128, len(text.split()) * 4))
                gen_kwargs = dict(
                    max_new_tokens=default_max_new_tokens,
                    temperature=0.0,
                    do_sample=False,
                    num_beams=default_num_beams,
                    early_stopping=True,
                )
                # Merge any explicit overrides
                gen_kwargs.update(gen_overrides)

                if cls._loader is None:
                    raise RuntimeError("Model loader is not initialized")
                # Ensure max_new_tokens is an int and pass it explicitly to satisfy the model loader's signature
                if "max_new_tokens" in gen_kwargs:
                    max_new_tokens = int(gen_kwargs["max_new_tokens"])
                else:
                    max_new_tokens = None
                # Prepare kwargs for generate_text excluding max_new_tokens and ensure proper typing
                pass_kwargs: Dict[str, Any] = {k: v for k, v in gen_kwargs.items() if k != "max_new_tokens"}
                # Call generate_text with max_new_tokens only when it's known to be an int
                if max_new_tokens is not None:
                    raw = cls._loader.generate_text(prompt, max_new_tokens=int(max_new_tokens), **pass_kwargs)
                else:
                    raw = cls._loader.generate_text(prompt, **pass_kwargs)

                # Post-process the model reply to extract only the corrected text portion
                def _extract_corrected_text(raw_text: str, original: str) -> str:
                    import re

                    if not raw_text:
                        return original

                    # Prefer the new explicit markers first: conservative then aggressive
                    # Prefer the last occurrence of each marker in case the model repeated the prompt
                    cons_matches = re.findall(r"===CONSERVATIVE===(.*?)===END_CONSERVATIVE===", raw_text, flags=re.S)
                    aggr_matches = re.findall(r"===AGGRESSIVE===(.*?)===END_AGGRESSIVE===", raw_text, flags=re.S)
                    cons_text = cons_matches[-1].strip() if cons_matches else None
                    aggr_text = aggr_matches[-1].strip() if aggr_matches else None

                    def _clean_candidate(s: str) -> str:
                        # Remove accidental surrounding quotes or stray trailing words like 'Explanation'
                        s = s.strip()
                        # drop leading/trailing single or double quotes
                        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                            s = s[1:-1].strip()
                        # remove a trailing lone apostrophe
                        if s.endswith("'"):
                            s = s[:-1].strip()
                        # remove common trailing markers or words introduced by the model
                        s = re.split(r"\nExplanation$|\nTo correct the OCR text:|\nThe task is to", s)[0].strip()
                        # normalize whitespace
                        s = re.sub(r"\s+", " ", s)
                        return s

                    # If conservative present and different from original, prefer it (cleaned)
                    if cons_text:
                        cons_text = _clean_candidate(cons_text)
                        if cons_text and cons_text != original:
                            return cons_text
                    # Otherwise, if aggressive present, prefer it (cleaned)
                    if aggr_text:
                        aggr_text = _clean_candidate(aggr_text)
                        if aggr_text:
                            return aggr_text

                    # Fallback to previous heuristics: search for an explicit 'Corrected text:' marker
                    m = re.search(r"Corrected text[:\\s]*\\n?\\s*(.*)", raw_text, flags=re.I | re.S)
                    if m:
                        candidate = m.group(1).strip()
                        candidate = re.split(r"\\n\\n|\\nThe OCR Post-Correction Assistant", candidate)[0].strip()
                        q = re.search(r"'''(.*?)'''", candidate, flags=re.S)
                        if q:
                            return q.group(1).strip()
                        return candidate

                    # Try triple-quoted block
                    q = re.search(r"'''(.*?)'''", raw_text, flags=re.S)
                    if q:
                        return q.group(1).strip()

                    # Fallback: return last non-empty line, but prefer content different from original
                    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
                    if not lines:
                        return original
                    candidate = lines[-1]
                    if candidate == original and len(lines) >= 2:
                        candidate = lines[-2]
                    return candidate

                corrected = _extract_corrected_text(raw, text)

                # Inspect both conservative/aggressive candidates to decide if fallback is needed
                import re
                cons_matches = re.findall(r"===CONSERVATIVE===(.*?)===END_CONSERVATIVE===", raw, flags=re.S)
                aggr_matches = re.findall(r"===AGGRESSIVE===(.*?)===END_AGGRESSIVE===", raw, flags=re.S)
                cons_text = cons_matches[-1].strip() if cons_matches else None
                aggr_text = aggr_matches[-1].strip() if aggr_matches else None

                def _clean(s: Optional[str]) -> Optional[str]:
                    if not s:
                        return None
                    return (s.strip().strip("'\"") if s else s)

                cons_text_clean = _clean(cons_text)
                aggr_text_clean = _clean(aggr_text)

                # If conservative result is missing or identical to original, perform a focused AGGRESSIVE-only second pass
                aggressive_fallback_used = False
                if not cons_text_clean or cons_text_clean == text:
                    try:
                        # Build a short Turkish aggressive prompt that asks only for the aggressive correction
                        aggr_prompt = (
                            "AGRESİF DÜZELTME YAPIN. Aşağıdaki OCR metnini tam olarak onarın; gerekirse kelime ekleyin.\n"
                            f"Orijinal OCR metni:\n'''{text}'''\n\n"
                            "Yanıtınızı yalnızca şu formatta verin ve başka hiç bir şey yazmayın:\n"
                            "===AGGRESSIVE===<düzgün metin>===END_AGGRESSIVE===\n"
                        )

                        aggr_gen_max = max(64, len(text.split()) * 4)
                        # keep generation conservative for resource reasons but allow the model to guess words
                        # Allow a small amount of stochasticity so the model can guess missing words
                        aggr_raw = cls._loader.generate_text(
                            aggr_prompt,
                            max_new_tokens=aggr_gen_max,
                            temperature=0.2,
                            do_sample=True,
                            num_beams=1,
                        )
                        # extract last aggressive marker
                        am = re.findall(r"===AGGRESSIVE===(.*?)===END_AGGRESSIVE===", aggr_raw, flags=re.S)
                        if am:
                            candidate = am[-1].strip()
                            candidate = re.sub(r"\s+", " ", candidate).strip("'\" ")
                            if candidate and candidate != text:
                                aggr_text_clean = candidate
                                aggressive_fallback_used = True
                        # attach debug raw output if requested
                        if input_json.get("debug"):
                            # include both original raw and aggressive raw
                            raw_combined = raw + "\n---AGGRESSIVE_FALLBACK_RAW---\n" + aggr_raw
                            raw = raw_combined
                    except Exception:
                        # ignore fallback errors and continue with previous result
                        pass

                # Choose the best available text: prefer conservative if it changed original, otherwise aggressive fallback or aggressive from first pass, else original
                final_text = None
                if cons_text_clean and cons_text_clean != text:
                    final_text = cons_text_clean
                elif aggressive_fallback_used and aggr_text_clean:
                    final_text = aggr_text_clean
                elif aggr_text_clean and aggr_text_clean != text:
                    final_text = aggr_text_clean
                else:
                    final_text = text

                # If final text is still identical to original, try fuzzy fallback
                if final_text == text:
                    try:
                        domain = input_json.get("domain_lexicon") or []
                        fb_text, fb_corrections = fuzzy_correct_text(text, domain_lexicon=domain)
                        if fb_corrections:
                            final_text = fb_text
                            if input_json.get("debug"):
                                raw = (raw or "") + "\n---FUZZY_FALLBACK_REPLACEMENTS---\n" + str(fb_corrections)
                    except Exception:
                        pass

                entry: Dict[str, Any] = {"page": page, "corrected_text": final_text}
                if input_json.get("debug"):
                    entry["raw_model_output"] = raw
                corrections.append(entry)
            except Exception:
                tb = traceback.format_exc()
                corrections.append({"page": page, "corrected_text": text, "note": "post-correction failed: " + tb})

        result = {"document_id": input_json.get("document_id"), "post_corrections": corrections}
        PostCorrectionExpert.validate_output(result)
        return result


def execute(input_json: Dict[str, Any]) -> Dict[str, Any]:
    return PostCorrectionExpert.execute(input_json)
