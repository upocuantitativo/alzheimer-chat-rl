"""
LLM client wrapper.

Backends supported (in order of preference):
    1. Groq Cloud (free tier) — set GROQ_API_KEY in .env
    2. Ollama (local)          — set OLLAMA_HOST
    3. HuggingFace Inference   — set HF_TOKEN
    4. Echo (no-op fallback)   — used when no backend available

The "Echo" backend keeps the pipeline runnable when offline or unconfigured —
the patient simulator still works in pure-rules mode in that case.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    text: str
    backend: str
    latency_s: float
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None


class LLMClient:
    """Lightweight multi-backend LLM client.

    Public API: client.chat(system, user, **kw) -> LLMResponse
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
        timeout: float = 30.0,
    ):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        self.backend = backend or self._autodetect_backend()
        self.model = model or self._default_model_for(self.backend)

    @staticmethod
    def _autodetect_backend() -> str:
        if os.getenv("GROQ_API_KEY"):
            return "groq"
        if os.getenv("OLLAMA_HOST"):
            return "ollama"
        if os.getenv("HF_TOKEN"):
            return "huggingface"
        return "echo"

    @staticmethod
    def _default_model_for(backend: str) -> str:
        return {
            "groq": os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            "ollama": os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            "huggingface": os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct"),
            "echo": "echo",
        }[backend]

    def chat(
        self,
        system: str,
        user: str,
        *,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        t0 = time.time()
        T = self.temperature if temperature is None else temperature
        N = self.max_tokens if max_tokens is None else max_tokens

        if self.backend == "groq":
            text = self._chat_groq(system, user, T, N)
        elif self.backend == "ollama":
            text = self._chat_ollama(system, user, T, N)
        elif self.backend == "huggingface":
            text = self._chat_hf(system, user, T, N)
        else:
            text = self._chat_echo(user)

        return LLMResponse(text=text, backend=self.backend, latency_s=time.time() - t0)

    # --------------------------------------------------------------
    # Backends
    # --------------------------------------------------------------
    def _chat_groq(self, system: str, user: str, T: float, N: int) -> str:
        api_key = os.environ["GROQ_API_KEY"]
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": T,
            "max_tokens": N,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        r = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if r.status_code != 200:
            raise LLMError(f"Groq error {r.status_code}: {r.text[:200]}")
        return r.json()["choices"][0]["message"]["content"].strip()

    def _chat_ollama(self, system: str, user: str, T: float, N: int) -> str:
        host = os.environ["OLLAMA_HOST"].rstrip("/")
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": T, "num_predict": N},
        }
        r = requests.post(f"{host}/api/chat", json=payload, timeout=self.timeout)
        if r.status_code != 200:
            raise LLMError(f"Ollama error {r.status_code}: {r.text[:200]}")
        return r.json()["message"]["content"].strip()

    def _chat_hf(self, system: str, user: str, T: float, N: int) -> str:
        token = os.environ["HF_TOKEN"]
        url = f"https://api-inference.huggingface.co/models/{self.model}"
        prompt = f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n"
        payload = {
            "inputs": prompt,
            "parameters": {"temperature": T, "max_new_tokens": N, "return_full_text": False},
        }
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if r.status_code != 200:
            raise LLMError(f"HF error {r.status_code}: {r.text[:200]}")
        data = r.json()
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()
        return str(data).strip()

    @staticmethod
    def _chat_echo(user: str) -> str:
        """Deterministic no-LLM fallback. The simulator handles its own rule-based
        generation; this echo only marks that the LLM path was unavailable."""
        return "[echo: sin LLM disponible — usando reglas]"


_default: Optional[LLMClient] = None


def get_default_client() -> LLMClient:
    global _default
    if _default is None:
        _default = LLMClient()
    return _default
