from __future__ import annotations


def test_07_models_list(client):
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    body = r.json()
    assert len(body["models"]) == 5
    assert all(x["available"] for x in body["models"])


def test_08_model_detail_known(client):
    r = client.get("/api/v1/models/yield")
    assert r.status_code == 200
    assert r.json()["model_key"] == "yield"
    assert r.json()["available"] is True


def test_09_model_detail_unknown_is_non_crashing(client):
    r = client.get("/api/v1/models/not-a-model")
    assert r.status_code == 200
    body = r.json()
    assert body["available"] is False
    assert body["error"] == "Unknown model key"


def test_10_reload_models_without_api_key_gate_when_disabled(client, fake_services):
    r = client.post("/api/v1/models/reload")
    assert r.status_code == 200
    assert "models" in r.json()
    assert fake_services.model.reloaded == 1
