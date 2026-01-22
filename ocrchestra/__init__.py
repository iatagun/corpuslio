"""OCRchestra package initializer.

Ollama-based document processing orchestra system.
"""
from .ollama_client import OllamaClient
from .ollama_orchestrator import OllamaOrchestrator, process_file

__all__ = [
    "OllamaClient",
    "OllamaOrchestrator",
    "process_file",
]
