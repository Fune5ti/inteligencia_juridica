from fastapi import APIRouter, Depends
from ..application.extract_service import (
	ExtractRequest,
	ExtractResponse,
	get_extract_service,
	ExtractService,
)
from ..infrastructure.pdf_downloader import get_pdf_downloader
from ..infrastructure.gemini_client import get_gemini_client
from ..infrastructure.auth import require_api_key

api_router = APIRouter()


@api_router.post("/extract", response_model=ExtractResponse, dependencies=[Depends(require_api_key)])
async def extract_endpoint(
	payload: ExtractRequest,
	pdf_downloader=Depends(get_pdf_downloader),
	gemini_client=Depends(get_gemini_client),
) -> ExtractResponse:
	service = get_extract_service(pdf_downloader=pdf_downloader, gemini_client=gemini_client)
	return await service.extract(payload)

