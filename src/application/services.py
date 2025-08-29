from __future__ import annotations
from pydantic import BaseModel
from typing import Any
from ..domain.repositories import ILlmClient


class LlmRequest(BaseModel):
    prompt: str


class LlmResponse(BaseModel):
    output: str


class LlmService:
    def __init__(self, client: ILlmClient):
        self._client = client

    async def generate(self, data: LlmRequest) -> LlmResponse:
        output = await self._client.generate(data.prompt)
        return LlmResponse(output=output)
