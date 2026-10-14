from __future__ import annotations

import pytest


def test_29_catalog(client):
    r = client.get("/api/v1/catalog")
    assert r.status_code == 200
    assert len(r.json()["datasets"]) == 4


def test_30_genotypes_default_paging(client):
    r = client.get("/api/v1/genotypes")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert body["limit"] == 50


def test_31_genotypes_query_and_domain_filter(client):
    r = client.get("/api/v1/genotypes", params={"query": "G1", "domain": "tlb"})
    assert r.status_code == 200
    assert r.json()["items"][0]["genotype"] == "G1"
    assert "tlb" in r.json()["items"][0]["domains"]


def test_32_genotypes_limit_bounds(client):
    assert client.get("/api/v1/genotypes", params={"limit": 0}).status_code == 422
    assert client.get("/api/v1/genotypes", params={"limit": 501}).status_code == 422
    assert client.get("/api/v1/genotypes", params={"offset": -1}).status_code == 422


def test_33_genotype_detail_existing(client):
    r = client.get("/api/v1/genotypes/G1")
    assert r.status_code == 200
    assert set(r.json()["domains"]) >= {"yield", "tlb", "sdm"}


def test_34_genotype_detail_missing_404(client):
    r = client.get("/api/v1/genotypes/DOES-NOT-EXIST")
    assert r.status_code == 404


def test_35_experiments_default_and_filter(client):
    r = client.get("/api/v1/experiments", params={"domain": "yield", "query": "Y1"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_36_experiments_invalid_domain_is_safe(client):
    # Invalid domain is treated as all domains by the current endpoint contract.
    r = client.get("/api/v1/experiments", params={"domain": "not-a-domain"})
    assert r.status_code == 200


def test_37_observations_requires_domain(client):
    assert client.get("/api/v1/observations").status_code == 422


def test_38_observations_valid_filters(client):
    r = client.get("/api/v1/observations", params={"domain": "yield", "genotype": "G1", "variable": "grain_yield"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.parametrize("domain", ["invalid", "Yield", ""])
def test_39_observations_invalid_domain_rejected(client, domain):
    assert client.get("/api/v1/observations", params={"domain": domain}).status_code == 422


def test_40_tlb_data(client):
    r = client.get("/api/v1/disease/tlb", params={"genotype": "G1"})
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_41_sdm_data(client):
    r = client.get("/api/v1/disease/sdm", params={"genotype": "G1"})
    assert r.status_code == 200
    assert r.json()["total"] == 1


def test_42_observation_paging_bounds(client):
    assert client.get("/api/v1/observations", params={"domain": "yield", "limit": 0}).status_code == 422
    assert client.get("/api/v1/observations", params={"domain": "yield", "limit": 1001}).status_code == 422
    assert client.get("/api/v1/observations", params={"domain": "yield", "offset": -1}).status_code == 422
