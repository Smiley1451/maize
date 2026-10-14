from __future__ import annotations


def test_61_every_openapi_route_has_explicit_coverage(client):
    """Safety net: fail when a new API route is added but the test suite is not updated."""
    spec = client.get("/openapi.json").json()
    routes = {(method.upper(), path) for path, ops in spec["paths"].items() for method in ops if method in {"get", "post", "put", "patch", "delete"}}
    expected = {
        ("GET", "/health"), ("GET", "/ready"),
        ("GET", "/api/v1/info"), ("GET", "/api/v1/features"), ("GET", "/api/v1/status"),
        ("GET", "/api/v1/models"), ("GET", "/api/v1/models/{model_key}"), ("POST", "/api/v1/models/reload"),
        ("POST", "/api/v1/predict/yield"), ("POST", "/api/v1/predict/tlb"), ("POST", "/api/v1/predict/sdm"),
        ("POST", "/api/v1/predict/all"), ("POST", "/api/v1/predict/batch"),
        ("POST", "/api/v1/predict/batch-csv"), ("POST", "/api/v1/predict/batch-json"),
        ("GET", "/api/v1/catalog"), ("GET", "/api/v1/genotypes"), ("GET", "/api/v1/genotypes/{genotype}"),
        ("GET", "/api/v1/experiments"), ("GET", "/api/v1/observations"),
        ("GET", "/api/v1/disease/tlb"), ("GET", "/api/v1/disease/sdm"),
        ("GET", "/api/v1/clusters/status"), ("GET", "/api/v1/clusters/data"),
        ("GET", "/api/v1/weather/status"), ("GET", "/api/v1/explainability/{model_key}"),
        ("GET", "/api/v1/model-metrics"), ("GET", "/api/v1/dataset-summary/{domain}"),
        ("GET", "/api/v1/project/verification"), ("GET", "/api/v1/project/files"),
    }
    assert routes == expected
