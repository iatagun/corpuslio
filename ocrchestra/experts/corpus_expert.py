"""Corpus Expert Module for OCRchestra.

Handles text cleaning, linguistic analysis (POS, Lemma) using Ollama,
and exporting data for Label Studio.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base import ExpertBase

logger = logging.getLogger(__name__)


class CorpusExpert(ExpertBase):
    """Expert for corpus operations: Cleaning, Analysis, Export."""

    def __init__(self, client=None):
        """Initialize Corpus expert.

        Args:
            client: LLM client (OllamaClient or GroqClient)
        """
        self.client = client

    @staticmethod
    def is_available() -> bool:
        """Check if expert is available (always True as it uses standard libs)."""
        return True

    def clean_text(self, text: str) -> str:
        """Clean and normalize text.

        - Fixes excessive whitespace
        - Removes duplicate words
        - Fixes common OCR errors for Turkish
        - Removes duplicate sentences
        """
        if not text:
            return ""

        # Replace non-breaking spaces
        text = text.replace("\xa0", " ")
        
        # Common Turkish OCR corrections
        ocr_fixes = {
            'ş': ['sh', 'S'],
            'ı': ['i'],
            'ğ': ['g'],
            'ö': ['o'],
            'ü': ['u'],
            'ç': ['c'],
        }
        
        # Remove obvious duplicate consecutive words (OCR artifact)
        # e.g., "ayna ayna" -> "ayna"
        words = text.split()
        cleaned_words = []
        prev_word = None
        
        for word in words:
            # Skip if same as previous (case-insensitive duplicate)
            if prev_word and word.lower() == prev_word.lower():
                continue
            cleaned_words.append(word)
            prev_word = word
        
        text = ' '.join(cleaned_words)
        
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove duplicate sentences (from chunk overlap)
        sentences = re.split(r'([.!?])\s+', text)
        seen_sentences = set()
        unique_sentences = []
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i].strip()
            
            # Skip empty
            if not sentence:
                i += 1
                continue
            
            # Normalize for comparison (remove punctuation, lowercase)
            normalized = re.sub(r'[^\w\s]', '', sentence.lower())
            
            # Check if we've seen this sentence
            if normalized and normalized not in seen_sentences:
                seen_sentences.add(normalized)
                unique_sentences.append(sentence)
                # Add punctuation if it exists
                if i + 1 < len(sentences) and sentences[i + 1] in '.!?':
                    unique_sentences.append(sentences[i + 1])
                    i += 2
                else:
                    i += 1
            else:
                # Skip duplicate sentence
                i += 2 if (i + 1 < len(sentences) and sentences[i + 1] in '.!?') else 1
        
        text = ' '.join(unique_sentences)
        
        return text.strip()

    def analyze_with_ollama(self, text: str, chunk_size: int = 1000, max_tokens: int = 4096) -> List[Dict[str, Any]]:
        """Analyze text using Ollama (POS, Lemma) with confidence scores.

        Args:
            text: Input text
            chunk_size: Character limit for chunks to avoid context limits

        Returns:
            List of word analysis dicts with confidence scores
        """
        if not self.client:
            logger.warning("Client not provided, skipping analysis.")
            return []

        # Split text into chunks
        chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
        
        full_analysis = []
        
        system_prompt = (
            "You are a Turkish linguistics expert. Analyze the following text and return ONLY a valid JSON array. "
            "Do NOT include explanations, markdown, or any extra text.\n\n"

            "For each token, return an object with:\n"
            "- 'word': surface form exactly as in the text\n"
            "- 'lemma': dictionary base form (sözlük biçimi, kök)\n"
            "- 'pos': one of [NOUN, VERB, ADJ, ADV, PRON, DET, CONJ, ADP, PUNCT, NUM]\n"
            "- 'confidence': float between 0.0 and 1.0\n\n"

            "Turkish-specific rules:\n"
            "- 'O' is DET when modifying a noun (o kitap), PRON when standing alone (o geldi)\n"
            "- 'gibi', 'için', 'ile' are ADP (postpositions), not CONJ\n"
            "- Words ending with -me/-ma/-yen/-yan may be NOUN (deverbal) depending on usage\n"
            "- If a token could reasonably belong to more than one POS, choose the best one AND lower confidence\n\n"

            "Confidence guidelines:\n"
            "- Clear and unambiguous: 0.85–1.0\n"
            "- Mild ambiguity: 0.6–0.85\n"
            "- Strong ambiguity / context-dependent: < 0.6\n\n"

            "CRITICAL:\n"
            "- Output MUST be a raw JSON array only\n"
            "- Start with '[' and end with ']'\n"
            "- No comments, no explanations, no code blocks"
        )

        for i, chunk in enumerate(chunks):
            logger.info("Analyzing chunk %d/%d...", i+1, len(chunks))
            
            prompt = f"Analyze this Turkish text:\n\n{chunk}"
            
            try:
                response = self.client.generate(
                    prompt=prompt,
                    system=system_prompt,
                    temperature=0.0,
                    max_tokens=max_tokens
                )
                
                # Parse JSON from response - handle markdown and explanatory text
                # Models like llama3.2 often wrap in ``` blocks and add commentary
                
                logger.info("Response length: %d chars", len(response))
                
                # First, try to extract from code blocks
                code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response, re.IGNORECASE)
                if code_block_match:
                    response_clean = code_block_match.group(1)
                    logger.info("Found code block, extracted %d chars", len(response_clean))
                else:
                    # No code block, use full response
                    response_clean = response
                    logger.info("No code block found, using full response")
                
                # Now find the JSON array - use GREEDY matching to get full array
                # Pattern: [ ... ] with anything inside (greedy)
                json_match = re.search(r'\[[\s\S]*\]', response_clean, re.DOTALL)
                
                if json_match:
                    logger.info("Regex matched %d chars of JSON", len(json_match.group(0)))
                    try:
                        json_str = json_match.group(0)
                        chunk_analysis = json.loads(json_str)
                        
                        # Validate it's a list of dicts
                        if isinstance(chunk_analysis, list) and len(chunk_analysis) > 0:
                            # Add pattern-based flags
                            chunk_analysis = self._add_pattern_flags(chunk_analysis)
                            full_analysis.extend(chunk_analysis)
                            logger.info("Successfully parsed %d items from chunk %d", len(chunk_analysis), i+1)
                        else:
                            logger.warning("Parsed JSON but got unexpected format for chunk %d", i)
                            
                    except json.JSONDecodeError as je:
                        logger.warning("JSON decode error for chunk %d: %s", i, je)
                        logger.info("Attempted JSON (first 300 chars): %s", json_match.group(0)[:300])
                else:
                    logger.warning("Could not find JSON array in chunk %d response", i)
                    logger.info("Raw response START (500 chars): %s", response[:500])
                    logger.info("Raw response END (500 chars): %s", response[-500:])
                    
                    # Fallback: try to extract words manually
                    try:
                        # Emergency fallback - extract from code block or text
                        text_to_analyze = code_block_match.group(1) if code_block_match else response
                        words = text_to_analyze.split()
                        fallback_analysis = [
                            {"word": w, "lemma": w.lower(), "pos": "UNK", "confidence": 0.3, "needs_review": True}
                            for w in words if w.isalnum() and len(w) > 1
                        ][:50]
                        if fallback_analysis:
                            logger.info("Using fallback word extraction (%d words) for chunk %d", len(fallback_analysis), i)
                            full_analysis.extend(fallback_analysis)
                    except Exception as fallback_err:
                        logger.error("Fallback extraction failed: %s", fallback_err)
                    
            except Exception as e:
                logger.error("Analysis failed for chunk %d: %s", i, e)

        # Remove duplicates from chunk overlaps
        full_analysis = self._deduplicate_analysis(full_analysis)
        
        return full_analysis

    def _deduplicate_analysis(self, analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate entries from analysis (caused by chunk overlaps).
        
        Args:
            analysis: List of analysis items
            
        Returns:
            Deduplicated analysis
        """
        seen = set()
        unique_analysis = []
        
        for item in analysis:
            if not isinstance(item, dict):
                continue
            
            # Create unique key from word + position estimate
            word = item.get('word', '').lower()
            
            # Simple deduplication: if we see the same word consecutively, skip
            if word and word != seen:
                unique_analysis.append(item)
            
            seen = word
        
        return unique_analysis

    def _add_pattern_flags(self, analysis: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add flags for problematic patterns (Turkish-specific).
        
        Args:
            analysis: List of analysis items
            
        Returns:
            Updated analysis with flags
        """
        problematic_words = {
            "o": {"issue": "DET vs PRON", "warn": "Context-dependent: check if subject or determiner"},
            "gibi": {"issue": "ADP not CONJ", "warn": "Usually postposition in Turkish"},
            "için": {"issue": "ADP not CONJ", "warn": "Postposition in Turkish"},
            "ile": {"issue": "ADP not CONJ", "warn": "Postposition in Turkish"},
        }
        
        for item in analysis:
            if not isinstance(item, dict):
                continue
                
            word = item.get('word', '').lower()
            
            # Check problematic words
            if word in problematic_words:
                if 'confidence' not in item or item.get('confidence', 1.0) > 0.6:
                    item['confidence'] = 0.5  # Force low confidence
                item['warning'] = problematic_words[word]['warn']
                item['needs_review'] = True
            
            # Check deverbal nouns (me/ma endings)
            elif word.endswith(('me', 'ma', 'mek', 'mak')):
                if item.get('pos') == 'VERB':
                    item['warning'] = "May be deverbal NOUN, not VERB"
                    item['needs_review'] = True
                    if 'confidence' not in item:
                        item['confidence'] = 0.6
            
            # Check participles (yan/yen endings)
            elif word.endswith(('yan', 'yen', 'dik', 'dık', 'duk', 'dük')):
                if item.get('pos') in ['ADJ', 'VERB']:
                    item['warning'] = "Participle (sıfat-fiil) - check morphology"
                    item['needs_review'] = True
                    if 'confidence' not in item:
                        item['confidence'] = 0.65
            
            # Ensure all items have confidence (default high if not flagged)
            if 'confidence' not in item:
                item['confidence'] = 0.9
            
            # Set needs_review based on confidence
            if item.get('confidence', 1.0) < 0.6:
                item['needs_review'] = True
            else:
                item['needs_review'] = item.get('needs_review', False)
        
        return analysis

    def export_to_label_studio(
        self, 
        text: str, 
        analysis: List[Dict[str, Any]], 
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export to Label Studio JSON format.

        This creates a task compatible with Label Studio's 'HyperText' or 'Text' interface.
        For simple corpus viewing, we inject the analysis into a predictable structure.
        """
        
        # Basic Label Studio Task Structure
        task = {
            "data": {
                "text": text,
                "meta_info": {
                    "word_count": len(text.split()),
                    "analysis_count": len(analysis)
                }
            },
            # We can add pre-annotations if we want to visualize POS tags immediately
            "predictions": [] 
        }

        # If we have analysis, we can try to map it to regions if we had character offsets.
        # Since Ollama generation might not perfectly align with original text character offsets,
        # precise "region" prediction is risky.
        # Instead, let's put the analysis in a separate metadata field or a custom format.
        
        # For this request "derlem içinde göstersene", the user likely wants to see the ANALYSIS.
        # Let's add the full analysis as a huge JSON object in data so it can be viewed in Label Studio's data view.
        task["data"]["analysis"] = analysis

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            # Label Studio expects a LIST of tasks for import
            with open(out, 'w', encoding='utf-8') as f:
                json.dump([task], f, ensure_ascii=False, indent=2)
            logger.info("Label Studio export saved to: %s", output_path)

        return task
