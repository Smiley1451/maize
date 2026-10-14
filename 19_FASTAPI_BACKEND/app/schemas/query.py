from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class ObservationQuery(BaseModel):
    domain: str | None = None
    genotype: str | None = None
    experiment: str | None = None
    variable: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
