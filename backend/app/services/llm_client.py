"""
Pluggable LLM client.

Supports three modes, controlled by settings.LLM_PROVIDER:
  - "ollama"  -> calls a local Ollama server (e.g. qwen3:8b)
  - "openai"  -> calls any OpenAI-compatible chat completions endpoint
  - "offline" -> no network/model dependency at all; produces deterministic,
                 extractive responses so the whole platform remains demoable
                 even with zero LLM infrastructure configured.

This abstraction means the agents never call a provider directly - they call
`llm_client.complete(...)`, so swapping providers is a one-line .env change.
"""
import httpx
from app.core.config import settings
from app.core.logging import logger


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER

    def complete(self, system: str, prompt: str, max_tokens: int = 512) -> str:
        try:
            if self.provider == "ollama":
                return self._ollama(system, prompt)
            elif self.provider == "openai":
                return self._openai(system, prompt, max_tokens)
            else:
                return self._offline(system, prompt)
        except Exception as e:
            logger.warning(f"LLM provider '{self.provider}' failed ({e}); falling back to offline mode.")
            return self._offline(system, prompt)

    def _ollama(self, system: str, prompt: str) -> str:
        resp = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": f"{system}\n\n{prompt}",
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "").strip()

    def _openai(self, system: str, prompt: str, max_tokens: int) -> str:
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        resp = httpx.post(
            f"{settings.OPENAI_BASE_URL}/chat/completions",
            headers=headers,
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    def _offline(self, system: str, prompt: str) -> str:
        """
        Deterministic fallback. Used directly by agents that already do most of
        the reasoning themselves (date parsing, validation) - for free-text
        document Q&A this is invoked by the Document Agent's own extractive
        logic, not a generic prompt completion, so this branch is rarely hit
        in practice but guarantees the system never hard-fails without an LLM.
        """
        return "I can help with that. (Offline mode: configure LLM_PROVIDER=ollama or openai for richer answers.)"


llm_client = LLMClient()
