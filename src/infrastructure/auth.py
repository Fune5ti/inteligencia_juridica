from __future__ import annotations
from fastapi import Header, HTTPException, status, Depends
from .settings import get_settings

API_KEY_HEADER = "X-API-Key"


def get_api_key(x_api_key: str | None = Header(default=None, alias=API_KEY_HEADER)) -> str:
    settings = get_settings()
    allowed = settings.api_keys()
    if not allowed:  
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")
    if not x_api_key or x_api_key not in allowed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return x_api_key


def require_api_key(api_key: str = Depends(get_api_key)) -> str:  
    return api_key

__all__ = ["require_api_key", "get_api_key", "API_KEY_HEADER"]
