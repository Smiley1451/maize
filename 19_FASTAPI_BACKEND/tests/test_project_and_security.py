from __future__ import annotations


def test_54_project_verification(client):
    r = client.get("/api/v1/project/verification")
    assert r.status_code == 200
    assert "project_root" in r.json()
    assert "available_artifacts" in r.json()


def test_55_project_files_root(client):
    r = client.get("/api/v1/project/files", params={"limit": 5})
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 5


def test_56_project_files_missing_prefix(client):
    r = client.get("/api/v1/project/files", params={"prefix": "DOES_NOT_EXIST"})
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_57_project_files_limit_is_capped(client):
    r = client.get("/api/v1/project/files", params={"limit": 5000})
    assert r.status_code == 200


def test_58_request_id_header_is_present(client):
    r = client.get("/health", headers={"X-Request-ID": "test-request-123"})
    assert r.status_code == 200
    assert r.headers["X-Request-ID"] == "test-request-123"


def test_59_api_key_protection_when_enabled(client, monkeypatch):
    import app.main as main_module
    import app.core.security as security_module

    monkeypatch.setattr(main_module, "API_KEY", "secret-key")
    monkeypatch.setattr(security_module, "API_KEY", "secret-key")

    protected = client.post("/api/v1/models/reload")
    assert protected.status_code == 401

    protected = client.post("/api/v1/models/reload", headers={"X-API-Key": "wrong"})
    assert protected.status_code == 401

    protected = client.post("/api/v1/models/reload", headers={"X-API-Key": "secret-key"})
    assert protected.status_code == 200


def test_60_public_health_stays_accessible_when_api_key_enabled(client, monkeypatch):
    import app.main as main_module
    monkeypatch.setattr(main_module, "API_KEY", "secret-key")
    r = client.get("/health")
    assert r.status_code == 200
