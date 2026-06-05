"""Run a Postman collection and produce an AI-assisted QA report.

Each transaction gets two layers of judgement:
  - deterministic checks (status code, transport errors, latency) that are always
    reliable, and
  - an LLM verdict (PASS/WARN/FAIL + anomalies + summary) for the nuanced stuff.

The two are merged so the worst signal wins, and the report stays useful even if
the LLM backend is unavailable.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from typing import Any

from . import llm
from .runner import Transaction, run_collection

_RANK = {"PASS": 0, "WARN": 1, "FAIL": 2}
SLOW_MS = 2000.0


def _deterministic(tx: Transaction) -> dict:
    anomalies, status = [], "PASS"
    if not tx.ok:
        return {"status": "FAIL", "anomalies": [f"Request failed: {tx.error}"]}
    if tx.status is not None and tx.status >= 500:
        status = "FAIL"; anomalies.append(f"Server error {tx.status}")
    elif tx.status is not None and tx.status >= 400:
        status = "FAIL"; anomalies.append(f"Client error {tx.status}")
    if tx.latency_ms > SLOW_MS:
        status = max(status, "WARN", key=_RANK.get)
        anomalies.append(f"Slow response: {tx.latency_ms:.0f} ms")
    return {"status": status, "anomalies": anomalies}


def _merge(det: dict, ai: dict) -> dict:
    status = max(det["status"], ai["status"], key=_RANK.get)
    anomalies = det["anomalies"] + [a for a in ai.get("anomalies", []) if a not in det["anomalies"]]
    return {
        "status": status,
        "severity": ai.get("severity", "low"),
        "anomalies": anomalies,
        "summary": ai.get("summary", ""),
    }


def analyze_collection(
    collection: dict,
    provider: str | None = None,
    model: str | None = None,
    variables: dict[str, str] | None = None,
    max_requests: int = 50,
    use_llm: bool = True,
) -> dict[str, Any]:
    transactions = run_collection(collection, variables=variables, max_requests=max_requests)
    provider = provider or llm.DEFAULT_PROVIDER
    model = model or (llm.default_model(provider) if use_llm else None)

    def assess(tx: Transaction) -> dict:
        det = _deterministic(tx)
        ai = llm.analyze(asdict(tx), provider, model) if use_llm else \
            {"status": "PASS", "severity": "low", "anomalies": [], "summary": ""}
        merged = _merge(det, ai)
        return {
            "name": tx.name, "folder": tx.folder, "method": tx.method, "url": tx.url,
            "status_code": tx.status, "latency_ms": tx.latency_ms,
            "verdict": merged["status"], "severity": merged["severity"],
            "anomalies": merged["anomalies"], "summary": merged["summary"],
        }

    if use_llm and len(transactions) > 1:
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(assess, transactions))
    else:
        results = [assess(t) for t in transactions]

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for r in results:
        counts[r["verdict"]] += 1
    latencies = [t.latency_ms for t in transactions if t.ok]

    return {
        "summary": {
            "total": len(results),
            "passed": counts["PASS"], "warnings": counts["WARN"], "failed": counts["FAIL"],
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
            "provider": provider if use_llm else "none",
            "model": model,
            "collection": collection.get("info", {}).get("name", "Untitled"),
        },
        "results": results,
    }
