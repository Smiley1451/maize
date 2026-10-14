from __future__ import annotations


def test_01_health_contract(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert {"project_root", "api_version"} <= body.keys()


def test_02_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
    assert isinstance(r.json()["project_root_exists"], bool)


def test_03_info(client):
    r = client.get("/api/v1/info")
    assert r.status_code == 200
    assert {"name", "version", "models", "datasets"} <= r.json().keys()


def test_04_features(client):
    r = client.get("/api/v1/features")
    assert r.status_code == 200
    body = r.json()
    assert len(body["base_features"]) == 7
    assert body["aliases_supported"]["plant_height_cm"] == "plant_height"
    assert "ear_height_ratio" in body["engineered_features"]


def test_05_status(client):
    r = client.get("/api/v1/status")
    assert r.status_code == 200
    body = r.json()
    assert body["api"] == "UP"
    assert body["models_available"] == body["models_total"]


def test_06_openapi_and_docs(client):
    for path in ["/openapi.json", "/docs", "/redoc"]:
        r = client.get(path)
        assert r.status_code == 200, path
    spec = client.get("/openapi.json").json()
    assert len(spec["paths"]) >= 25
