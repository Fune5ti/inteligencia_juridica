from __future__ import annotations
from typing import Any

from ..domain.repositories import ILlmClient


class DummyLlmClient:
    async def generate(self, prompt: str, **kwargs: Any) -> str:  
        return f"Echo: {prompt}"


def get_dummy_llm_client() -> ILlmClient:
    return DummyLlmClient()
