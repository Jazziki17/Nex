"""
Tests for the Kai API Server
===============================
Tests REST endpoints and WebSocket connectivity.
Uses FastAPI's TestClient for HTTP and WebSocket testing.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kai.api.server import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def _allow_tmp_paths(tmp_path, monkeypatch):
    """Allow tmp_path in the file routes' ALLOWED_ROOTS."""
    import kai.api.routes.files as files_mod
    import kai.api.routes.spreadsheets as ss_mod

    monkeypatch.setattr(files_mod, "ALLOWED_ROOTS", [Path.home(), tmp_path])
    monkeypatch.setattr(ss_mod, "_safe_path", lambda p: _tmp_safe_path(p, tmp_path))


def _tmp_safe_path(path_str: str, tmp_path: Path) -> Path:
    """Safe path that also allows tmp_path."""
    resolved = Path(path_str).expanduser().resolve()
    for root in [Path.home().resolve(), tmp_path.resolve()]:
        if str(resolved).startswith(str(root)):
            return resolved
    raise ValueError(f"Path not within allowed directories: {path_str}")


def test_status_endpoint(client):
    """Test /api/status returns valid JSON with expected fields."""
    response = client.get("/api/status")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert "uptime" in data
    assert isinstance(data["uptime"], (int, float))


def test_files_list_home(client):
    """Test /api/files/list can list the home directory."""
    response = client.post("/api/files/list", json={"path": "~"})
    assert response.status_code == 200

    data = response.json()
    assert "entries" in data
    assert isinstance(data["entries"], list)


def test_files_list_with_pattern(client):
    """Test /api/files/list with a glob pattern."""
    response = client.post("/api/files/list", json={"path": "~", "pattern": ".*"})
    assert response.status_code == 200

    data = response.json()
    assert "entries" in data


def test_files_write_and_read(client, tmp_path):
    """Test writing and reading a file via the API."""
    test_file = str(tmp_path / "test_api.txt")

    # Write
    response = client.post("/api/files/write", json={
        "path": test_file,
        "content": "Hello from API test!",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    # Read
    response = client.post("/api/files/read", json={"path": test_file})
    assert response.status_code == 200
    assert response.json()["content"] == "Hello from API test!"


def test_files_rename(client, tmp_path):
    """Test renaming a file via the API."""
    old = tmp_path / "old_name.txt"
    old.write_text("rename me")
    new = str(tmp_path / "new_name.txt")

    response = client.post("/api/files/rename", json={
        "old_path": str(old),
        "new_path": new,
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_files_delete(client, tmp_path):
    """Test deleting a file via the API."""
    target = tmp_path / "to_delete.txt"
    target.write_text("delete me")

    response = client.post("/api/files/delete", json={"path": str(target)})
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert not target.exists()


def test_files_read_not_found(client, tmp_path):
    """Test reading a nonexistent file returns 404."""
    response = client.post("/api/files/read", json={
        "path": str(tmp_path / "nonexistent_kai_test_file.txt"),
    })
    assert response.status_code == 404


def test_commands_allowed_list(client):
    """Test /api/commands/allowed returns the allowlist."""
    response = client.get("/api/commands/allowed")
    assert response.status_code == 200

    data = response.json()
    assert "allowed_commands" in data
    assert "ls" in data["allowed_commands"]


def test_commands_run_allowed(client):
    """Test running an allowed command."""
    response = client.post("/api/commands/run", json={"command": "echo hello"})
    assert response.status_code == 200

    data = response.json()
    assert data["exit_code"] == 0
    assert "hello" in data["stdout"]


def test_commands_run_blocked(client):
    """Test that disallowed commands are rejected."""
    response = client.post("/api/commands/run", json={"command": "rm -rf /"})
    assert response.status_code == 403


def test_websocket_connection(client):
    """Test WebSocket connects and receives welcome message."""
    with client.websocket_connect("/ws") as ws:
        data = ws.receive_json()
        assert data["type"] == "connected"
        assert "message" in data["data"]


def test_websocket_ping(client):
    """Test WebSocket ping/pong."""
    with client.websocket_connect("/ws") as ws:
        # Consume welcome message
        ws.receive_json()

        # Send ping
        ws.send_json({"type": "ping"})
        data = ws.receive_json()
        assert data["type"] == "pong"


def test_spreadsheet_csv(client, tmp_path):
    """Test creating a CSV file via the API."""
    csv_path = str(tmp_path / "test.csv")

    response = client.post("/api/files/spreadsheet", json={
        "path": csv_path,
        "headers": ["Name", "Age", "City"],
        "rows": [["Alice", 30, "NYC"], ["Bob", 25, "LA"]],
        "format": "csv",
    })
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["rows"] == 2

    # Verify file was created
    read_response = client.post("/api/files/read", json={"path": csv_path})
    assert read_response.status_code == 200
    assert "Alice" in read_response.json()["content"]
