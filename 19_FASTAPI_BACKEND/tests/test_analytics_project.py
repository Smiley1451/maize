from __future__ import annotations

import pytest


def test_43_clusters_status(client):
    r = client.get("/api/v1/clusters/status")
    assert r.status_code == 200
    assert r.json()["available"] is True


def test_44_clusters_data_existing(client):
    r = client.get("/api/v1/clusters/data", params={"filename": "GENOTYPE_CLUSTERS.csv", "limit": 1})
    assert r.status_code == 200
    assert r.json()["total"] == 2
    assert len(r.json()["items"]) == 1


def test_45_clusters_data_missing_file_is_safe(client):
    r = client.get("/api/v1/clusters/data", params={"filename": "missing.csv"})
    assert r.status_code == 200
    assert r.json()["available"] is False


def test_46_weather_status(client):
    r = client.get("/api/v1/weather/status")
    assert r.status_code == 200
    assert "files" in r.json()


@pytest.mark.parametrize("model_key", ["yield", "tlb_regression", "tlb_classifier", "sdm_regression", "sdm_classifier", "unknown"])
def test_47_explainability_endpoint(client, model_key):
    r = client.get(f"/api/v1/explainability/{model_key}")
    assert r.status_code == 200
    assert r.json()["model_key"] == model_key


@pytest.mark.parametrize("domain,kind", [
    ("yield", "regression"),
    ("tlb", "regression"),
    ("tlb", "classification"),
    ("sdm", "regression"),
    ("sdm", "classification"),
])
def test_48_model_metrics_valid_combinations(client, domain, kind):
    r = client.get("/api/v1/model-metrics", params={"domain": domain, "kind": kind})
    assert r.status_code == 200
    assert r.json()["domain"] == domain
    assert r.json()["kind"] == kind


def test_49_model_metrics_invalid_domain(client):
    assert client.get("/api/v1/model-metrics", params={"domain": "invalid"}).status_code == 422


def test_50_model_metrics_invalid_kind(client):
    assert client.get("/api/v1/model-metrics", params={"domain": "yield", "kind": "invalid"}).status_code == 422


@pytest.mark.parametrize("domain", ["yield", "tlb", "sdm", "multi_trait"])
def test_51_dataset_summary(client, domain):
    r = client.get(f"/api/v1/dataset-summary/{domain}")
    assert r.status_code == 200
    assert r.json()["available"] is True
    assert r.json()["rows"] >= 1


def test_52_dataset_summary_invalid_domain(client):
    r = client.get("/api/v1/dataset-summary/invalid")
    assert r.status_code == 400


def test_53_dataset_summary_metric_integrity(client):
    r = client.get("/api/v1/dataset-summary/yield")
    assert r.status_code == 200
    numeric = r.json()["numeric_summary"]
    assert any(row["feature"] == "value_numeric" for row in numeric)
