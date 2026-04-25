import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import brain
from fastapi.testclient import TestClient


class DummyMessage:
    def __init__(self, content: str):
        self.content = content


class DummyChoice:
    def __init__(self, content: str):
        self.message = DummyMessage(content)


class DummyResponse:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]


class DummyCompletions:
    def __init__(self, content: str = "return 1;", should_raise: bool = False):
        self.content = content
        self.should_raise = should_raise

    def create(self, **kwargs):
        if self.should_raise:
            raise RuntimeError("upstream unavailable")
        return DummyResponse(self.content)


class DummyChat:
    def __init__(self, completions):
        self.completions = completions


class DummyClient:
    def __init__(self, completions):
        self.chat = DummyChat(completions)


def make_client(ai_content: str = "return data?.items?.length ?? 0;", should_raise: bool = False):
    return DummyClient(DummyCompletions(content=ai_content, should_raise=should_raise))


def reset_log():
    brain.evolution_log.clear()


def test_security_scan_flags_and_allows_clean_code():
    assert brain.security_scan("window.location.href") == r"\bwindow\."
    assert brain.security_scan("const x = data?.items ?? [];") is None


def test_build_prompt_includes_error_and_code_context():
    prompt = brain.build_prompt("Cannot read x", "return data.items.map(x => x.id);")
    assert "Cannot read x" in prompt
    assert "return data.items.map" in prompt
    assert "Return ONLY the corrected function body" in prompt


def test_root_and_log_endpoints_work_and_limit_entries():
    reset_log()
    client = TestClient(brain.app)

    for i in range(55):
        brain.evolution_log.append({
            "worker_id": f"W-{i}",
            "outcome": "evolved" if i % 2 == 0 else "rejected",
        })

    root = client.get("/")
    assert root.status_code == 200
    payload = root.json()
    assert payload["status"] == "online"
    assert payload["evolutions"] == 28
    assert payload["rejections"] == 27

    log_payload = client.get("/log")
    assert log_payload.status_code == 200
    entries = log_payload.json()["log"]
    assert len(entries) == 50
    assert entries[0]["worker_id"] == "W-5"


def test_evolve_rejects_invalid_json_and_missing_fields():
    reset_log()
    client = TestClient(brain.app)

    bad_json = client.post("/evolve", data="not-json", headers={"content-type": "application/json"})
    assert bad_json.status_code == 400
    assert bad_json.json()["detail"] == "Invalid JSON body"

    missing = client.post("/evolve", json={"error": "x"})
    assert missing.status_code == 400
    assert "required" in missing.json()["detail"]


def test_evolve_success_strips_markdown_fences_and_logs(monkeypatch):
    reset_log()
    monkeypatch.setattr(brain, "client", make_client("```js\nreturn data?.x ?? 0;\n```"))
    client = TestClient(brain.app)

    response = client.post(
        "/evolve",
        json={
            "error": "Cannot read properties of null",
            "code": "return data.items.length;",
            "worker_id": "W-100",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "evolved"
    assert payload["logic"] == "return data?.x ?? 0;"
    assert payload["model"] == brain.MODEL
    assert brain.evolution_log[-1]["outcome"] == "evolved"
    assert brain.evolution_log[-1]["worker_id"] == "W-100"


def test_evolve_rejects_banned_patch_and_records_reason(monkeypatch):
    reset_log()
    monkeypatch.setattr(brain, "client", make_client("return window.location.href;"))
    client = TestClient(brain.app)

    response = client.post(
        "/evolve",
        json={"error": "boom", "code": "return x", "worker_id": "W-200"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rejected"
    assert "Security violation detected" in payload["reason"]
    assert brain.evolution_log[-1]["outcome"] == "rejected"
    assert brain.evolution_log[-1]["reason"] == r"\bwindow\."


def test_evolve_returns_502_when_ai_synthesis_fails(monkeypatch):
    reset_log()
    monkeypatch.setattr(brain, "client", make_client(should_raise=True))
    client = TestClient(brain.app)

    response = client.post(
        "/evolve",
        json={"error": "boom", "code": "return x", "worker_id": "W-500"},
    )

    assert response.status_code == 502
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["detail"] == "AI synthesis failed"
    assert brain.evolution_log[-1]["outcome"] == "error"
