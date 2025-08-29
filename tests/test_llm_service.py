import asyncio
import pytest
from src.application.services import LlmService, LlmRequest
from src.infrastructure.dummy_llm_client import get_dummy_llm_client


@pytest.mark.asyncio
async def test_llm_service_generates_output():
    service = LlmService(client=get_dummy_llm_client())
    resp = await service.generate(LlmRequest(prompt="Hello"))
    assert resp.output == "Echo: Hello"
