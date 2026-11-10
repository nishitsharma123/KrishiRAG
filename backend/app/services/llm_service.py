"""
LLM Service — Phase 4
Manages connection to local Ollama instance running Qwen3 4B.

Enforces:
- Single-concurrency local inference (threading.Lock + asyncio.Semaphore)
- Low temperature (0.1 - 0.2) for strictly factual grounded generation
- Streaming and non-streaming responses
- Model availability and health checking
- Comprehensive timeout and graceful error reporting
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM operations."""
    pass


class LLMConnectionError(LLMServiceError):
    """Raised when Ollama daemon is unreachable."""
    pass


class LLMModelUnavailableError(LLMServiceError):
    """Raised when the specified model is not pulled in Ollama."""
    pass


class LLMService:
    """Singleton service for Ollama Qwen3 4B inference."""

    _instance: Optional["LLMService"] = None
    _lock = threading.Lock()
    _async_semaphore: Optional[asyncio.Semaphore] = None

    def __new__(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def async_semaphore(self) -> asyncio.Semaphore:
        if self._async_semaphore is None:
            self._async_semaphore = asyncio.Semaphore(1)
        return self._async_semaphore

    def is_available(self) -> Dict[str, Any]:
        """
        Check whether the Ollama server is running and the target model is installed.
        """
        url = f"{settings.OLLAMA_BASE_URL}/api/tags"
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return {
                        "available": False,
                        "error": f"Ollama returned HTTP {resp.status_code}",
                        "models": [],
                    }
                data = resp.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                target_model = settings.OLLAMA_MODEL
                # Check if target model (e.g. 'qwen3:4b' or 'qwen3:4b:latest') is installed
                model_found = any(target_model in m or m in target_model for m in models)
                return {
                    "available": True,
                    "ollama_available": True,
                    "system_ready": model_found,
                    "target_model": target_model,
                    "model_name": target_model,
                    "model_installed": model_found,
                    "installed_models": models,
                }
        except httpx.ConnectError:
            return {
                "available": False,
                "ollama_available": False,
                "system_ready": False,
                "model_installed": False,
                "model_name": settings.OLLAMA_MODEL,
                "error": f"Cannot connect to Ollama at {settings.OLLAMA_BASE_URL}. Is 'ollama serve' running?",
                "models": [],
            }
        except Exception as e:
            return {
                "available": False,
                "ollama_available": False,
                "system_ready": False,
                "model_installed": False,
                "model_name": settings.OLLAMA_MODEL,
                "error": str(e),
                "models": [],
            }

    def generate_chat_sync(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """
        Synchronous generation with single-concurrency lock.
        """
        with self._lock:
            url = f"{settings.OLLAMA_BASE_URL}/api/chat"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx": settings.OLLAMA_CONTEXT_WINDOW,
                    "num_predict": max_tokens,
                },
            }

            try:
                with httpx.Client(timeout=float(settings.LLM_TIMEOUT_SECONDS)) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 404:
                        raise LLMModelUnavailableError(
                            f"Model '{settings.OLLAMA_MODEL}' not found in Ollama. Run: ollama pull {settings.OLLAMA_MODEL}"
                        )
                    if resp.status_code != 200:
                        raise LLMServiceError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

                    data = resp.json()
                    content = data.get("message", {}).get("content", "")
                    return content
            except httpx.ConnectError as e:
                raise LLMConnectionError(
                    f"Failed to connect to Ollama at {settings.OLLAMA_BASE_URL}: {str(e)}"
                )
            except httpx.TimeoutException as e:
                raise LLMServiceError(
                    f"LLM generation timed out after {settings.LLM_TIMEOUT_SECONDS}s: {str(e)}"
                )

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> str:
        """
        Asynchronous generation bounded by asyncio.Semaphore(1).
        """
        async with self.async_semaphore:
            url = f"{settings.OLLAMA_BASE_URL}/api/chat"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_ctx": settings.OLLAMA_CONTEXT_WINDOW,
                    "num_predict": max_tokens,
                },
            }

            try:
                async with httpx.AsyncClient(timeout=float(settings.LLM_TIMEOUT_SECONDS)) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 404:
                        raise LLMModelUnavailableError(
                            f"Model '{settings.OLLAMA_MODEL}' not found in Ollama. Run: ollama pull {settings.OLLAMA_MODEL}"
                        )
                    if resp.status_code != 200:
                        raise LLMServiceError(f"Ollama returned HTTP {resp.status_code}: {resp.text}")

                    data = resp.json()
                    content = data.get("message", {}).get("content", "")
                    return content
            except httpx.ConnectError as e:
                raise LLMConnectionError(
                    f"Failed to connect to Ollama at {settings.OLLAMA_BASE_URL}: {str(e)}"
                )
            except httpx.TimeoutException as e:
                raise LLMServiceError(
                    f"LLM generation timed out after {settings.LLM_TIMEOUT_SECONDS}s: {str(e)}"
                )

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming token generator yielding partial text chunks in real-time.
        """
        async with self.async_semaphore:
            url = f"{settings.OLLAMA_BASE_URL}/api/chat"
            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_ctx": settings.OLLAMA_CONTEXT_WINDOW,
                    "num_predict": max_tokens,
                },
            }

            try:
                async with httpx.AsyncClient(timeout=float(settings.LLM_TIMEOUT_SECONDS)) as client:
                    async with client.stream("POST", url, json=payload) as response:
                        if response.status_code != 200:
                            raise LLMServiceError(f"Ollama stream error: HTTP {response.status_code}")
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    chunk = json.loads(line)
                                    token = chunk.get("message", {}).get("content", "")
                                    if token:
                                        yield token
                                except json.JSONDecodeError:
                                    continue
            except httpx.ConnectError as e:
                raise LLMConnectionError(
                    f"Failed to connect to Ollama at {settings.OLLAMA_BASE_URL}: {str(e)}"
                )


# Module-level singleton
llm_service = LLMService()
