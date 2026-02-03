"""Ollama Orchestra - Ana Orkestratör.

Çeşitli dosya formatlarını analiz eder ve uygun uzman modülleri çağırarak
metin çıkarımı yapar. Ollama dil modelleri ile çalışır.
"""
from __future__ import annotations

import json
import logging
import mimetypes
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .ollama_client import OllamaClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class OllamaOrchestrator:
    """Main orchestrator for document processing using Ollama models."""

    SUPPORTED_FORMATS = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".doc": "docx",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".tiff": "image",
        ".tif": "image",
        ".bmp": "image",
        ".txt": "text",
    }

    def __init__(
        self,
        conductor_model: str = "llama3.2:3b",
        vision_model: str = "llava",
        ollama_host: str = "http://localhost:11434",
    ):
        """Initialize orchestrator.

        Args:
            conductor_model: Model for orchestration decisions
            vision_model: Model for image OCR (requires llava)
            ollama_host: Ollama server address
        """
        self.conductor_model = conductor_model
        self.vision_model = vision_model
        self.client = OllamaClient(
            host=ollama_host,
            default_model=conductor_model,
        )
        
        # Lazy-loaded experts
        self._pdf_expert = None
        self._docx_expert = None
        self._image_expert = None

    @property
    def pdf_expert(self):
        """Lazy load PDF expert."""
        if self._pdf_expert is None:
            from .experts.pdf_expert import PDFExpert
            self._pdf_expert = PDFExpert(ollama_client=self.client)
        return self._pdf_expert

    @property
    def docx_expert(self):
        """Lazy load DOCX expert."""
        if self._docx_expert is None:
            from .experts.docx_expert import DOCXExpert
            self._docx_expert = DOCXExpert()
        return self._docx_expert

    @property
    def corpus_expert(self):
        """Lazy load Corpus expert."""
        from .experts.corpus_expert import CorpusExpert
        return CorpusExpert(client=self.client)

    def detect_format(self, file_path: Union[str, Path]) -> str:
        """Detect file format.

        Args:
            file_path: Path to file

        Returns:
            Format type: 'pdf', 'docx', 'image', 'text', or 'unknown'
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        return self.SUPPORTED_FORMATS.get(ext, "unknown")

    def process(
        self,
        file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Any]:
        """Process a single file and extract text.

        Args:
            file_path: Path to input file
            output_path: Optional path for .txt output

        Returns:
            Dict with extraction result and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Dosya bulunamadı: {file_path}",
                "file": str(file_path),
            }

        format_type = self.detect_format(file_path)
        logger.info("İşleniyor: %s (format: %s)", file_path.name, format_type)

        result = {
            "file": str(file_path),
            "format": format_type,
        }

        # Route to appropriate expert
        if format_type == "pdf":
            extraction = self.pdf_expert.extract_text(file_path)
        elif format_type == "docx":
            extraction = self.docx_expert.extract_text(file_path)
        elif format_type == "image":
            extraction = self._process_image(file_path)
        elif format_type == "text":
            extraction = self._read_text_file(file_path)
        else:
            extraction = {
                "success": False,
                "error": f"Desteklenmeyen format: {file_path.suffix}",
                "text": "",
            }

        result.update(extraction)

        # Save to output file if requested
        if output_path and result.get("success"):
            self._save_output(result.get("text", ""), output_path)
            result["output_file"] = str(output_path)

        return result

    def process_and_export(
        self,
        file_path: Union[str, Path],
        export_format: str = "label_studio",
        output_path: Optional[Union[str, Path]] = None,
        analyze: bool = True
    ) -> Dict[str, Any]:
        """Process file and export to specific format.

        Args:
            file_path: Input file path
            export_format: Export format (default: label_studio)
            output_path: Output file path for the export
            analyze: Whether to run linguistic analysis (POS/Lemma)

        Returns:
            Result dictionary
        """
        # 1. Extract Text
        result = self.process(file_path)
        if not result.get("success"):
            return result

        text = result.get("text", "")
        
        # 2. Clean Text
        cleaned_text = self.corpus_expert.clean_text(text)
        
        # 3. Analyze (Optional)
        analysis = []
        if analyze:
            logger.info("Linguistic analysis started (this may take time)...")
            analysis = self.corpus_expert.analyze_with_ollama(cleaned_text)

        # 4. Export
        if export_format == "label_studio":
            if not output_path:
                # Default: input_name.json
                p = Path(file_path)
                output_path = p.with_suffix(".json")
            
            self.corpus_expert.export_to_label_studio(
                text=cleaned_text, 
                analysis=analysis, 
                output_path=str(output_path)
            )
            result["export_file"] = str(output_path)
            result["analysis_count"] = len(analysis)

        return result

    def process_batch(
        self,
        file_paths: List[Union[str, Path]],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> List[Dict[str, Any]]:
        """Process multiple files.

        Args:
            file_paths: List of input file paths
            output_dir: Directory for .txt outputs

        Returns:
            List of extraction results
        """
        results = []
        output_dir = Path(output_dir) if output_dir else None
        
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        for file_path in file_paths:
            file_path = Path(file_path)
            
            output_path = None
            if output_dir:
                output_path = output_dir / f"{file_path.stem}.txt"

            result = self.process(file_path, output_path)
            results.append(result)

        return results

    def _process_image(self, image_path: Path) -> Dict[str, Any]:
        """Process image file using vision model.

        Args:
            image_path: Path to image file

        Returns:
            Extraction result
        """
        # Check if vision model is available
        available_models = [m.get("name", "") for m in self.client.list_models()]
        has_vision = any("llava" in m.lower() for m in available_models)

        if not has_vision:
            return {
                "success": False,
                "error": (
                    "Görüntü OCR için llava modeli gerekli. "
                    "Lütfen çalıştırın: ollama pull llava"
                ),
                "text": "",
            }

        try:
            prompt = (
                "Read and transcribe ALL text visible in this image. "
                "Write every word exactly as it appears. Output only the text."
            )
            
            text = self.client.generate_with_image(
                prompt=prompt,
                image_path=image_path,
                model=self.vision_model,
            )
            
            return {
                "success": True,
                "text": text.strip(),
                "method": "vision_ocr",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Vision OCR hatası: {e}",
                "text": "",
            }

    def _read_text_file(self, text_path: Path) -> Dict[str, Any]:
        """Read plain text file.

        Args:
            text_path: Path to text file

        Returns:
            File contents
        """
        try:
            text = text_path.read_text(encoding="utf-8")
            return {
                "success": True,
                "text": text,
                "method": "direct_read",
            }
        except UnicodeDecodeError:
            try:
                text = text_path.read_text(encoding="latin-1")
                return {
                    "success": True,
                    "text": text,
                    "method": "direct_read",
                    "encoding": "latin-1",
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Dosya okunamadı: {e}",
                    "text": "",
                }

    def _save_output(self, text: str, output_path: Union[str, Path]) -> None:
        """Save text to output file.

        Args:
            text: Text content to save
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        logger.info("Kaydedildi: %s", output_path)

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status and available experts.

        Returns:
            Status information
        """
        # Check Ollama connection
        ollama_available = self.client.is_available()
        models = self.client.list_models() if ollama_available else []
        model_names = [m.get("name", "") for m in models]

        # Check experts
        from .experts.pdf_expert import PDFExpert
        from .experts.docx_expert import DOCXExpert

        return {
            "ollama_available": ollama_available,
            "ollama_host": self.client.host,
            "conductor_model": self.conductor_model,
            "vision_model": self.vision_model,
            "available_models": model_names,
            "has_vision": any("llava" in m.lower() for m in model_names),
            "experts": {
                "pdf": PDFExpert.is_available(),
                "docx": DOCXExpert.is_available(),
            },
            "supported_formats": list(self.SUPPORTED_FORMATS.keys()),
        }


# Convenience function
def process_file(file_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """Quick process function."""
    orch = OllamaOrchestrator()
    return orch.process(file_path, output_path)
