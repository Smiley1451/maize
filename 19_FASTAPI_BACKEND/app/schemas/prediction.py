from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class MaizeInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    genotype: str = Field(default="UNKNOWN", min_length=1)
    days_to_50_percent_pollen_shedding: float | None = Field(default=None, ge=0, le=200)
    days_to_50_percent_silking: float | None = Field(default=None, ge=0, le=200)
    days_to_75_percent_dry_husk: float | None = Field(default=None, ge=0, le=250)
    plant_height: float | None = Field(default=None, ge=0, le=500)
    ear_height: float | None = Field(default=None, ge=0, le=400)
    plant_stand: float | None = Field(default=None, ge=0, le=250_000)
    plant_stand_000_per_ha: float | None = Field(default=None, ge=0, le=250)
    shelling_percentage: float | None = Field(default=None, ge=0, le=100)


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    genotype: str
    results: dict[str, Any]
    model_status: dict[str, str]
    warnings: list[str] = []


class BatchPredictionRequest(BaseModel):
    records: list[MaizeInput] = Field(min_length=1, max_length=500)


class ModelInfo(BaseModel):
    model_key: str
    available: bool
    path: str | None = None
    package_type: str | None = None
    feature_count: int | None = None
    features: list[str] = []
