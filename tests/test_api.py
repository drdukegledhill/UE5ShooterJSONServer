from fastapi.testclient import TestClient
from app.main import app
import app.storage as storage
import json


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_post_telemetry(tmp_path):
    # Redirect storage to a temp directory so tests don't touch repo data
    storage.DATA_DIR = tmp_path
    storage.DATA_FILE = tmp_path / "data.jsonl"
    storage.LOCK_FILE = tmp_path / "data.jsonl.lock"

    client = TestClient(app)
    payload = {
        "session_id": "testsession",
        "timestamp": "2026-01-12T12:34:56Z",
        "event_type": "unit_test",
        "payload": {"k": "v"},
    }

    r = client.post("/api/telemetry", json=payload)
    assert r.status_code == 201
    assert r.json() == {"status": "accepted"}

    # Verify file written and valid
    assert storage.DATA_FILE.exists()
    lines = storage.DATA_FILE.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    obj = json.loads(lines[0])
    assert obj["session_id"] == "testsession"
    assert obj["event_type"] == "unit_test"
