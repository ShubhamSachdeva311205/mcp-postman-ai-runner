"""A dependency-light Postman collection runner.

The original project shelled out to Newman (Node). This is a native Python
runner: it parses a Postman v2.1 collection, resolves {{variables}}, executes
each request with httpx, and captures the request/response transaction. No Node,
no temp files, nothing persisted, which makes it portable (it runs the same way
locally, in the MCP server, and in a container) and easy to host.

We deliberately do NOT execute Postman's pre-request / test JavaScript: the
"testing" here is done by an LLM analysing the real responses, so all we need is
to faithfully send each request and record what came back.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

_VAR = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


@dataclass
class Transaction:
    name: str
    method: str
    url: str
    request_headers: dict[str, str]
    request_body: Any
    status: int | None
    response_headers: dict[str, str]
    response_body: str
    latency_ms: float
    ok: bool                      # transport-level success (got a response)
    error: str | None = None
    folder: str = ""


def _resolve(text: str, variables: dict[str, str]) -> str:
    if not isinstance(text, str):
        return text
    return _VAR.sub(lambda m: variables.get(m.group(1), m.group(0)), text)


def _collect_variables(collection: dict, extra: dict[str, str] | None) -> dict[str, str]:
    variables: dict[str, str] = {}
    for v in collection.get("variable", []) or []:
        if "key" in v:
            variables[v["key"]] = str(v.get("value", ""))
    if extra:
        variables.update({k: str(v) for k, v in extra.items()})
    return variables


def _build_url(url: Any, variables: dict[str, str]) -> str:
    if isinstance(url, str):
        return _resolve(url, variables)
    if isinstance(url, dict):
        if url.get("raw"):
            return _resolve(url["raw"], variables)
        host = url.get("host", [])
        host = ".".join(host) if isinstance(host, list) else str(host)
        path = url.get("path", [])
        path = "/".join(str(p) for p in path) if isinstance(path, list) else str(path)
        proto = url.get("protocol", "https")
        out = f"{proto}://{host}/{path}"
        return _resolve(out, variables)
    return ""


def _headers(req: dict, variables: dict[str, str]) -> dict[str, str]:
    out = {}
    for h in req.get("header", []) or []:
        if h.get("disabled"):
            continue
        out[_resolve(h.get("key", ""), variables)] = _resolve(h.get("value", ""), variables)
    return out


def _body(req: dict, variables: dict[str, str]):
    body = req.get("body") or {}
    mode = body.get("mode")
    if mode == "raw":
        return _resolve(body.get("raw", ""), variables)
    if mode == "urlencoded":
        return {_resolve(p["key"], variables): _resolve(p.get("value", ""), variables)
                for p in body.get("urlencoded", []) if not p.get("disabled")}
    if mode == "formdata":
        return {_resolve(p["key"], variables): _resolve(p.get("value", ""), variables)
                for p in body.get("formdata", []) if not p.get("disabled") and p.get("type") != "file"}
    return None


def _iter_items(items: list[dict], folder: str = ""):
    for item in items or []:
        if "item" in item:  # folder
            yield from _iter_items(item["item"], folder=item.get("name", folder))
        elif "request" in item:
            yield folder, item


def run_collection(
    collection: dict,
    variables: dict[str, str] | None = None,
    timeout: float = 20.0,
    max_requests: int = 50,
) -> list[Transaction]:
    """Execute every request in a parsed Postman collection. Returns one
    Transaction per request (capped at max_requests for safety)."""
    vars_ = _collect_variables(collection, variables)
    transactions: list[Transaction] = []

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        for folder, item in _iter_items(collection.get("item", [])):
            if len(transactions) >= max_requests:
                break
            req = item.get("request", {})
            if isinstance(req, str):
                req = {"method": "GET", "url": req}
            method = (req.get("method") or "GET").upper()
            url = _build_url(req.get("url"), vars_)
            headers = _headers(req, vars_)
            body = _body(req, vars_)
            name = item.get("name", url)

            kwargs: dict = {"headers": headers}
            if isinstance(body, str) and body:
                kwargs["content"] = body.encode()
            elif isinstance(body, dict) and body:
                ct = headers.get("Content-Type", "").lower()
                kwargs["data"] = body if "urlencoded" in ct or not ct else None
                if kwargs["data"] is None:
                    kwargs["data"] = body

            t0 = time.perf_counter()
            try:
                resp = client.request(method, url, **kwargs)
                latency = (time.perf_counter() - t0) * 1000
                text = resp.text
                transactions.append(Transaction(
                    name=name, method=method, url=url,
                    request_headers=headers, request_body=body,
                    status=resp.status_code,
                    response_headers=dict(resp.headers),
                    response_body=text[:8000],
                    latency_ms=round(latency, 1), ok=True, folder=folder,
                ))
            except Exception as exc:  # noqa: BLE001
                latency = (time.perf_counter() - t0) * 1000
                transactions.append(Transaction(
                    name=name, method=method, url=url,
                    request_headers=headers, request_body=body,
                    status=None, response_headers={}, response_body="",
                    latency_ms=round(latency, 1), ok=False,
                    error=str(exc), folder=folder,
                ))
    return transactions
