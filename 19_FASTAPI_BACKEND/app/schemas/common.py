from __future__ import annotations
from typing import Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    project_root: str
    api_version: str


class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[dict[str, Any]]


class ErrorResponse(BaseModel):
    detail: str
