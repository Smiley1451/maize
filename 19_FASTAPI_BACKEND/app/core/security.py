from __future__ import annotations

from fastapi import Header, HTTPException

from .config import API_KEY


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Optional API-key gate. Disabled when MAIZE_API_KEY is empty."""
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
