"""Gemma client. One function, three providers, no lock-in.

MODEL_PROVIDER picks where Gemma runs:
  aistudio   (default) hosted Gemma on Google AI Studio, needs GEMINI_API_KEY
  openrouter hosted Gemma on OpenRouter, needs OPENROUTER_API_KEY
  ollama     your own machine or server, needs OLLAMA_HOST
"""

import os

import httpx

DEFAULT_MODEL = "gemma-4-26b-a4b-it"


class LLMError(RuntimeError):
    pass


def generate(prompt: str, model: str | None = None, temperature: float = 0.7) -> str:
    provider = os.getenv("MODEL_PROVIDER", "aistudio").lower()
    model = model or os.getenv("MODEL_NAME") or DEFAULT_MODEL
    if provider == "aistudio":
        return _aistudio(prompt, model, temperature)
    if provider == "openrouter":
        return _openrouter(prompt, model, temperature)
    if provider == "ollama":
        return _ollama(prompt, model, temperature)
    raise LLMError(f"Unknown MODEL_PROVIDER {provider!r}; use aistudio, openrouter or ollama")


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise LLMError(f"{name} is not set; add it to .env (see .env.example)")
    return value


def _aistudio(prompt: str, model: str, temperature: float) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_require("GEMINI_API_KEY"))
    try:
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=temperature),
        )
    except Exception as exc:  # the SDK raises several error types; report them all the same way
        raise LLMError(f"AI Studio request failed: {exc}") from exc
    if not resp.text:
        raise LLMError("AI Studio returned an empty response")
    return resp.text


def _openrouter(prompt: str, model: str, temperature: float) -> str:
    try:
        resp = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {_require('OPENROUTER_API_KEY')}"},
            json={"model": model, "temperature": temperature,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        raise LLMError(f"OpenRouter request failed: {exc}") from exc


def _ollama(prompt: str, model: str, temperature: float) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    try:
        resp = httpx.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"temperature": temperature}},
            timeout=600,
        )
        resp.raise_for_status()
        return resp.json()["response"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise LLMError(f"Ollama request failed: {exc}") from exc
