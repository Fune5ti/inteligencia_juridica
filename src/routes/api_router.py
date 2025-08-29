from fastapi import APIRouter, Depends
from ..application.extract_service import (
	ExtractRequest,
	ExtractResponse,
	get_extract_service,
	ExtractService,
)

api_router = APIRouter()


@api_router.post("/extract", response_model=ExtractResponse)
async def extract_endpoint(
	payload: ExtractRequest, service: ExtractService = Depends(get_extract_service)
) -> ExtractResponse:
	return await service.extract(payload)

