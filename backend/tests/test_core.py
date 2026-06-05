import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app
from backend.core import llm
from backend.core.runner import _build_url, _iter_items, _resolve
from backend.core.analyze import _deterministic, _merge
from backend.core.runner import Transaction

client = TestClient(app)
SAMPLE = json.loads((Path(__file__).parent / "sample_collection.json").read_text())


def test_variable_resolution():
    assert _resolve("{{base}}/json", {"base": "https://x.test"}) == "https://x.test/json"
    assert _resolve("{{missing}}", {}) == "{{missing}}"  # left intact


def test_url_builder_forms():
    v = {"base": "https://x.test"}
    assert _build_url({"raw": "{{base}}/a"}, v) == "https://x.test/a"
    assert _build_url({"protocol": "https", "host": ["x", "test"], "path": ["a", "b"]}, v) == "https://x.test/a/b"


def test_iter_items_flattens_folders():
    coll = {"item": [{"name": "F", "item": [{"name": "R", "request": {"method": "GET", "url": "u"}}]}]}
    items = list(_iter_items(coll["item"]))
    assert len(items) == 1
    folder, item = items[0]
    assert folder == "F" and item["name"] == "R"


def test_sample_collection_parses_to_three():
    assert len(list(_iter_items(SAMPLE["item"]))) == 3


def test_deterministic_flags():
    err = Transaction("t", "GET", "u", {}, None, 500, {}, "", 10.0, True)
    assert _deterministic(err)["status"] == "FAIL"
    slow = Transaction("t", "GET", "u", {}, None, 200, {}, "", 5000.0, True)
    assert _deterministic(slow)["status"] == "WARN"
    ok = Transaction("t", "GET", "u", {}, None, 200, {}, "", 50.0, True)
    assert _deterministic(ok)["status"] == "PASS"


def test_merge_takes_worst_status():
    det = {"status": "FAIL", "anomalies": ["500"]}
    ai = {"status": "PASS", "severity": "low", "anomalies": [], "summary": "ok"}
    assert _merge(det, ai)["status"] == "FAIL"


def test_coerce_handles_fenced_json():
    out = llm._coerce('```json\n{"status":"warn","anomalies":["x"],"summary":"s"}\n```')
    assert out["status"] == "WARN" and out["anomalies"] == ["x"]


def test_info_endpoint():
    j = client.get("/api/info").json()
    assert "providers" in j and "ollama" in j["providers"]
    assert j["default_provider"] == "ollama"
