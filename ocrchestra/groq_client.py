"""Groq API Client for OCRchestra.

Provides integration with Groq's fast inference API for cloud deployment.
"""
import logging
from typing import Optional

from groq import Groq

logger = logging.getLogger(__name__)


class GroqClient:
    """Client for interacting with Groq API."""

    def __init__(
        self,
        api_key: str,
        default_model: str = "llama-3.3-70b-versatile",
        timeout: int = 120,
    ):
        """Initialize Groq client.
        
        Args:
            api_key: Groq API key
            default_model: Default model to use
            timeout: Request timeout in seconds
        """
        self.client = Groq(api_key=api_key, timeout=timeout)
        self.default_model = default_model
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
    ) -> str:
        """Generate text using Groq.

        Args:
            prompt: User prompt
            model: Model to use (defaults to default_model)
            system: System message
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        model = model or self.default_model
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error("Groq API error: %s", e)
            raise ConnectionError(f"Groq API request failed: {e}")

    def get_available_models(self):
        """Get list of available models."""
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ]
