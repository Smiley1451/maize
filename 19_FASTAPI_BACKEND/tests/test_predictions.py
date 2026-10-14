from __future__ import annotations

import io
import json

import pytest
from app.core.config import MAX_BATCH_ROWS

BASE = {
    "genotype": "G_TEST",
    "days_to_50_percent_pollen_shedding": 70,
    "days_to_50_percent_silking": 72,
    "days_to_75_percent_dry_husk": 112,
    "plant_height": 220,
    "ear_height": 110,
    "plant_stand": 70000,
    "shelling_percentage": 82,
}


def test_11_yield_prediction_contract(client):
    r = client.post("/api/v1/predict/yield", json=BASE)
    assert r.status_code == 200
    body = r.json()
    assert body["genotype"] == "G_TEST"
    assert body["model_status"]["yield"] == "OK"
    assert "yield_prediction_kg_ha" in body["results"]
    assert body["results"]["yield_range_flag"] == "OK"


def test_12_tlb_prediction_contract(client):
    r = client.post("/api/v1/predict/tlb", json=BASE)
    assert r.status_code == 200
    body = r.json()
    assert body["model_status"]["tlb_regression"] == "OK"
    assert body["model_status"]["tlb_classifier"] == "OK"
    assert 1 <= body["results"]["tlb_score_prediction"] <= 9


def test_13_sdm_prediction_contract(client):
    r = client.post("/api/v1/predict/sdm", json=BASE)
    assert r.status_code == 200
    body = r.json()
    assert body["model_status"]["sdm_regression"] == "OK"
    assert body["model_status"]["sdm_classifier"] == "OK"
    assert 0 <= body["results"]["sdm_pdi_prediction"] <= 100


def test_14_all_prediction_contains_all_domains(client):
    r = client.post("/api/v1/predict/all", json=BASE)
    assert r.status_code == 200
    body = r.json()
    expected = {
        "yield_prediction_kg_ha", "tlb_score_prediction", "tlb_reaction_prediction",
        "sdm_pdi_prediction", "sdm_reaction_prediction"
    }
    assert expected <= body["results"].keys()


def test_15_single_vs_batch_prediction_results_match(client):
    records = [
        BASE,
        {**BASE, "genotype": "G_TEST_2", "plant_height": 230, "ear_height": 120},
    ]
    singles = [client.post("/api/v1/predict/all", json=x).json()["results"] for x in records]
    batch = client.post("/api/v1/predict/batch", json={"records": records})
    assert batch.status_code == 200
    batch_items = batch.json()["results"]
    for single, item in zip(singles, batch_items):
        for key in ["yield_prediction_kg_ha", "tlb_score_prediction", "sdm_pdi_prediction", "tlb_reaction_prediction", "sdm_reaction_prediction"]:
            assert single[key] == item[key], key


def test_16_batch_empty_rejected(client):
    r = client.post("/api/v1/predict/batch", json={"records": []})
    assert r.status_code == 422


def test_17_batch_over_limit_rejected(client):
    records = [BASE] * (MAX_BATCH_ROWS + 1)
    r = client.post("/api/v1/predict/batch", json={"records": records})
    assert r.status_code == 422


@pytest.mark.parametrize("field,value", [
    ("days_to_50_percent_pollen_shedding", -1),
    ("days_to_50_percent_pollen_shedding", 201),
    ("plant_height", -1),
    ("plant_height", 501),
    ("shelling_percentage", -1),
    ("shelling_percentage", 101),
])
def test_18_invalid_numeric_bounds_rejected(client, field, value):
    payload = {**BASE, field: value}
    assert client.post("/api/v1/predict/yield", json=payload).status_code == 422


def test_19_empty_genotype_rejected(client):
    payload = {**BASE, "genotype": ""}
    assert client.post("/api/v1/predict/yield", json=payload).status_code == 422


def test_20_partial_input_is_explicitly_reported(client):
    r = client.post("/api/v1/predict/all", json={"genotype": "PARTIAL", "plant_height": 220})
    assert r.status_code == 200
    assert r.json()["results"]["input_completeness"] == "PARTIAL_INPUT_MODEL_IMPUTED"


def test_21_stand_alias_is_accepted(client):
    payload = {**BASE}
    payload.pop("plant_stand")
    payload["plant_stand_000_per_ha"] = 70
    r = client.post("/api/v1/predict/yield", json=payload)
    assert r.status_code == 200


def test_22_batch_csv_valid(client):
    csv = "genotype,plant_height,ear_height\nG1,220,110\nG2,230,115\n"
    r = client.post("/api/v1/predict/batch-csv", files={"file": ("data.csv", csv, "text/csv")})
    assert r.status_code == 200
    assert r.json()["count"] == 2


def test_23_batch_csv_wrong_extension(client):
    r = client.post("/api/v1/predict/batch-csv", files={"file": ("data.txt", "a,b\n1,2\n", "text/plain")})
    assert r.status_code == 400


def test_24_batch_csv_invalid_bytes(client):
    # A valid filename with bytes that are not decodable as a normal CSV.
    raw = b"\xff\xfe\xfa\x00"
    r = client.post("/api/v1/predict/batch-csv", files={"file": ("data.csv", raw, "text/csv")})
    assert r.status_code == 400


def test_25_batch_json_list_valid(client):
    body = json.dumps([BASE, {**BASE, "genotype": "G2"}])
    r = client.post("/api/v1/predict/batch-json", files={"file": ("data.json", body, "application/json")})
    assert r.status_code == 200
    assert r.json()["count"] == 2


def test_26_batch_json_object_valid(client):
    body = json.dumps(BASE)
    r = client.post("/api/v1/predict/batch-json", files={"file": ("data.json", body, "application/json")})
    assert r.status_code == 200
    assert r.json()["count"] == 1


def test_27_batch_json_wrong_extension(client):
    r = client.post("/api/v1/predict/batch-json", files={"file": ("data.txt", "{}", "application/json")})
    assert r.status_code == 400


def test_28_batch_json_malformed_content(client):
    r = client.post("/api/v1/predict/batch-json", files={"file": ("data.json", "not-json", "application/json")})
    assert r.status_code == 400
