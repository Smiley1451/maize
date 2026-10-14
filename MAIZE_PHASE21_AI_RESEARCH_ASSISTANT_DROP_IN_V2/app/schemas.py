from pydantic import BaseModel, Field
from typing import Any, Literal

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=10000)

class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5000)
    top_k: int = Field(default=8, ge=1, le=50)

class PredictionRequest(BaseModel):
    domain: Literal["yield","tlb","sdm","all"] = "all"
    features: dict[str, Any] = Field(default_factory=dict)
