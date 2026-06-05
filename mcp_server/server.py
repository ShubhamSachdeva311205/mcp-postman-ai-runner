"""MCP server: expose the Postman AI runner as tools for MCP clients
(Claude Desktop, etc.).

Run directly:  python -m mcp_server.server
Configure in an MCP client by pointing it at this module with the project's venv.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from backend.core import llm
from backend.core.analyze import analyze_collection

mcp = FastMCP("Postman AI Runner")


@mcp.tool()
def list_llm_providers() -> str:
    """List available LLM providers (ollama/gemini/claude), their installed
    Ollama models, and which need an API key."""
    return json.dumps(llm.available_providers(), indent=2)


@mcp.tool()
def run_postman_collection(
    collection_path: str,
    provider: str = "",
    model: str = "",
    use_llm: bool = True,
    max_requests: int = 50,
) -> str:
    """Run a Postman collection and return an AI-assisted QA report.

    Args:
        collection_path: absolute path to a Postman v2.1 collection .json file.
        provider: 'ollama' (default), 'gemini', or 'claude'. Empty = server default.
        model: model name; empty = provider default.
        use_llm: set False to skip LLM analysis (deterministic checks only).
        max_requests: cap on how many requests to execute.
    """
    path = Path(collection_path)
    if not path.is_absolute():
        return json.dumps({"error": "Provide an absolute path to the collection."})
    if not path.exists():
        return json.dumps({"error": f"File not found: {collection_path}"})
    try:
        collection = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"error": f"Could not parse collection JSON: {exc}"})

    report = analyze_collection(
        collection,
        provider=provider or None,
        model=model or None,
        max_requests=max_requests,
        use_llm=use_llm,
    )
    return json.dumps(report, indent=2)


if __name__ == "__main__":
    os.environ.setdefault("MCP_PROVIDER", "ollama")
    mcp.run()
