from __future__ import annotations
from fastapi import HTTPException, status, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from .settings import get_settings

API_KEY_HEADER = "X-API-Key"
_api_key_header = APIKeyHeader(name=API_KEY_HEADER, auto_error=False, description="API key issued by the service")


def get_api_key(x_api_key: str | None = Security(_api_key_header)) -> str:
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
