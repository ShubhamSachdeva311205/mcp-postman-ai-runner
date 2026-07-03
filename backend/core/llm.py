"""Pluggable LLM backend for analysing API transactions.

Providers: ollama (local, default, no key), gemini, claude. All are called over
plain HTTP so there are no heavy SDK dependencies and the same code runs locally,
in the MCP server, and in a container.

Each provider returns a normalised verdict:
    {status: PASS|WARN|FAIL, severity: low|medium|high,
     anomalies: [str, ...], summary: str}
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_PROVIDER = os.getenv("MCP_PROVIDER", "ollama")

_SYSTEM = (
    "You are a senior QA / API-testing engineer. Given one HTTP request and its "
    "response, judge whether the response is healthy. Flag anomalies: error "
    "status codes, error bodies, slow responses, missing/contradictory fields, "
    "security issues (leaked secrets, stack traces, permissive CORS), malformed "
    "payloads. Be concise and specific."
)

_JSON_INSTRUCTION = (
    'Respond with ONLY a JSON object: {"status": "PASS"|"WARN"|"FAIL", '
    '"severity": "low"|"medium"|"high", "anomalies": ["..."], '
    '"summary": "one sentence"}'
)


def _prompt(tx: dict[str, Any]) -> str:
    req = {
        "method": tx.get("method"), "url": tx.get("url"),
        "headers": tx.get("request_headers"), "body": tx.get("request_body"),
    }
    resp = {
        "status": tx.get("status"), "latency_ms": tx.get("latency_ms"),
        "headers": tx.get("response_headers"),
        "body": (tx.get("response_body") or "")[:4000],
        "transport_error": tx.get("error"),
    }
    return (
        f"{_SYSTEM}\n\nREQUEST:\n{json.dumps(req, indent=2)}\n\n"
        f"RESPONSE:\n{json.dumps(resp, indent=2)}\n\n{_JSON_INSTRUCTION}"
    )


def _coerce(raw: str) -> dict:
    """Best-effort extract a JSON verdict from model text."""
    if not raw:
        return _fallback("empty model response")
    raw = re.sub(r"```(json)?", "", raw).strip()
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            return _fallback(f"unparseable: {raw[:120]}")
        try:
            obj = json.loads(m.group(0))
        except json.JSONDecodeError:
            return _fallback(f"unparseable: {raw[:120]}")
    status = str(obj.get("status", "WARN")).upper()
    if status not in {"PASS", "WARN", "FAIL"}:
        status = "WARN"
    return {
        "status": status,
        "severity": str(obj.get("severity", "low")).lower(),
        "anomalies": [str(a) for a in obj.get("anomalies", []) if a],
        "summary": str(obj.get("summary", "")).strip(),
    }


def _fallback(msg: str) -> dict:
    return {"status": "WARN", "severity": "low", "anomalies": [msg],
            "summary": "Analysis unavailable."}


# --------------------------------------------------------------------------- #
def available_providers() -> dict[str, Any]:
    out = {
        "ollama": {"available": _ollama_up(), "models": list_ollama_models(), "needs_key": False},
        "gemini": {"available": bool(os.getenv("GEMINI_API_KEY")), "models": ["gemini-2.0-flash"], "needs_key": True},
        "claude": {"available": bool(os.getenv("ANTHROPIC_API_KEY")), "models": ["claude-sonnet-4-6"], "needs_key": True},
    }
    return out


def _ollama_up() -> bool:
    try:
        httpx.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def list_ollama_models() -> list[str]:
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def default_model(provider: str) -> str:
    if provider == "ollama":
        models = list_ollama_models()
        return os.getenv("OLLAMA_MODEL") or (models[0] if models else "llama3.1:8b")
    if provider == "gemini":
        return "gemini-2.0-flash"
    if provider == "claude":
        return "claude-sonnet-4-6"
    return ""


# --------------------------------------------------------------------------- #
def analyze(tx: dict[str, Any], provider: str | None = None, model: str | None = None,
            timeout: float = 120.0) -> dict:
    provider = provider or DEFAULT_PROVIDER
    model = model or default_model(provider)
    prompt = _prompt(tx)
    try:
        if provider == "ollama":
            raw = _call_ollama(prompt, model, timeout)
        elif provider == "gemini":
            raw = _call_gemini(prompt, model, timeout)
        elif provider == "claude":
            raw = _call_claude(prompt, model, timeout)
        else:
            return _fallback(f"unknown provider '{provider}'")
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"{provider} error: {exc}")
    verdict = _coerce(raw)
    verdict["provider"] = provider
    verdict["model"] = model
    return verdict


def _call_ollama(prompt: str, model: str, timeout: float) -> str:
    # think=False keeps "thinking" models (qwen3, gemma3, etc.) from putting their
    # answer in a separate `thinking` field and leaving `response` empty. We fall
    # back to `thinking` too, in case a model ignores the flag.
    body = {"model": model, "prompt": prompt, "stream": False,
            "format": "json", "think": False, "options": {"temperature": 0}}
    r = httpx.post(f"{OLLAMA_URL}/api/generate", json=body, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "") or data.get("thinking", "")


def _call_gemini(prompt: str, model: str, timeout: float) -> str:
    key = os.environ["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    r = httpx.post(url, json=body, timeout=timeout)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _call_claude(prompt: str, model: str, timeout: float) -> str:
    key = os.environ["ANTHROPIC_API_KEY"]
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": model, "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}]}
    r = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=body, timeout=timeout)
    r.raise_for_status()
    return r.json()["content"][0]["text"]
