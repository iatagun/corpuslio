"""Ollama API Client for OCRchestra.

Provides a wrapper around Ollama's REST API for text generation
and vision model inference. Uses localhost:11434 by default.
"""
from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        default_model: str = "llama3.2:3b",
        timeout: int = 120,
    ):
        self.host = host.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to Ollama API."""
        url = f"{self.host}{endpoint}"
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Ollama sunucusuna bağlanılamadı: {self.host}. "
                "Lütfen 'ollama serve' komutunun çalıştığından emin olun."
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Ollama isteği zaman aşımına uğradı ({self.timeout}s)"
            )

    def _post_stream(self, endpoint: str, payload: Dict[str, Any]) -> str:
        """Make a streaming POST request and collect full response."""
        url = f"{self.host}{endpoint}"
        payload["stream"] = True
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        full_response += data["response"]
                    if data.get("done", False):
                        break
            return full_response
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Ollama sunucusuna bağlanılamadı: {self.host}"
            )

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        url = f"{self.host}/api/tags"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get("models", [])
        except Exception as e:
            logger.warning("Model listesi alınamadı: %s", e)
            return []

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            requests.get(f"{self.host}/api/tags", timeout=5)
            return True
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text using Ollama.

        Args:
            prompt: The input prompt
            model: Model name (uses default if None)
            system: System prompt for context
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        
        if system:
            payload["system"] = system

        logger.debug("Ollama generate: model=%s, prompt_len=%d", model, len(prompt))
        return self._post_stream("/api/generate", payload)

    def generate_with_image(
        self,
        prompt: str,
        image_path: Union[str, Path],
        model: str = "llava",
        temperature: float = 0.1,
    ) -> str:
        """Generate text from image using vision model.

        Args:
            prompt: Text prompt describing what to do with the image
            image_path: Path to image file
            model: Vision model name (default: llava)
            temperature: Sampling temperature

        Returns:
            Generated text response
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Görüntü bulunamadı: {image_path}")

        # Read and encode image as base64
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "model": model,
            "prompt": prompt,
            "images": [image_data],
            "options": {
                "temperature": temperature,
            },
        }

        logger.debug("Ollama vision: model=%s, image=%s", model, image_path.name)
        return self._post_stream("/api/generate", payload)

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """Chat completion with message history.

        Args:
            messages: List of {"role": "user"|"assistant"|"system", "content": "..."}
            model: Model name
            temperature: Sampling temperature

        Returns:
            Assistant's response
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
            },
            "stream": False,
        }

        result = self._post("/api/chat", payload)
        return result.get("message", {}).get("content", "")


# Convenience function for quick generation
def generate(prompt: str, model: str = "llama3.2:3b", **kwargs) -> str:
    """Quick generate function."""
    client = OllamaClient(default_model=model)
    return client.generate(prompt, **kwargs)
