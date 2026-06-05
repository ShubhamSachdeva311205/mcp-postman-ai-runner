"""HTTP API for the MCP Postman AI runner dashboard.

  GET  /api/info   available LLM providers + installed Ollama models
  POST /api/run    run a Postman collection and return the AI QA report
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..core import llm
from ..core.analyze import analyze_collection

router = APIRouter()


class RunRequest(BaseModel):
    collection: dict[str, Any] = Field(..., description="Parsed Postman v2.1 collection JSON")
    provider: str | None = None
    model: str | None = None
    variables: dict[str, str] | None = None
    use_llm: bool = True
    max_requests: int = 50


@router.get("/info")
async def info():
    providers = llm.available_providers()
    return {
        "version": "1.0.0",
        "providers": providers,
        "default_provider": llm.DEFAULT_PROVIDER,
        "default_model": llm.default_model(llm.DEFAULT_PROVIDER),
    }


@router.post("/run")
async def run(req: RunRequest):
    if not req.collection.get("item"):
        raise HTTPException(400, "Collection has no requests (missing 'item' array).")
    if req.use_llm:
        prov = req.provider or llm.DEFAULT_PROVIDER
        avail = llm.available_providers().get(prov, {})
        if not avail.get("available"):
            raise HTTPException(
                400,
                f"Provider '{prov}' unavailable. "
                + ("Set its API key." if avail.get("needs_key") else "Is Ollama running?"),
            )
    try:
        return analyze_collection(
            req.collection, provider=req.provider, model=req.model,
            variables=req.variables, max_requests=req.max_requests, use_llm=req.use_llm,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Run failed: {exc}")
