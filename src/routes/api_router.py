from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
import uuid
import httpx
from ..application.extract_service import (
	ExtractRequest,
	ExtractResponse,
	get_extract_service,
	ExtractService,
)
from ..infrastructure.pdf_downloader import get_pdf_downloader
from ..infrastructure.gemini_client import get_gemini_client
from ..infrastructure.auth import require_api_key
from ..infrastructure.job_repository import ExtractionJobRepository

api_router = APIRouter(
	tags=["extraction"],
	responses={
		401: {"description": "Unauthorized – missing or invalid API key"},
		500: {"description": "Internal server error"},
	},
)


@api_router.post(
	"/extract",
	response_model=ExtractResponse,
	dependencies=[Depends(require_api_key)],
	summary="Synchronous extraction",
	description="Download the PDF, run structured extraction and return the result in a single response.",
	responses={
		200: {
			"description": "Successful extraction",
			"content": {
				"application/json": {
					"example": {
						"resume": "Resumo conciso do caso...",
						"timeline": [
							{
								"event_id": 0,
								"event_name": "Marco Inicial",
								"event_description": "Ajuizamento da ação...",
								"event_date": "22/10/2024",
								"event_page_init": 1,
								"event_page_end": 13
							}
						],
						"evidence": [
							{
								"evidence_id": 0,
								"evidence_name": "Procuração",
								"evidence_flaw": "Sem inconsistências",
								"evidence_page_init": 16,
								"evidence_page_end": 16
							}
						]
					}
				}
			},
		}
	},
)
async def extract_endpoint(
	payload: ExtractRequest,
	pdf_downloader=Depends(get_pdf_downloader),
	gemini_client=Depends(get_gemini_client),
) -> ExtractResponse:
	service = get_extract_service(pdf_downloader=pdf_downloader, gemini_client=gemini_client)
	return await service.extract(payload)


class AsyncExtractRequest(ExtractRequest):
	"""Request body for asynchronous extraction.

	callback_url (optional): Public URL to receive a POST webhook when the job finishes.
	"""
	callback_url: str | None = None


@api_router.post(
	"/extract/async",
	dependencies=[Depends(require_api_key)],
	summary="Asynchronous extraction (fire-and-poll / webhook)",
	description=(
		"Enqueue an extraction job. Returns a job identifier immediately. "
		"Use the job status endpoint to poll or provide a callback_url to receive a webhook when completed."
	),
	responses={
		200: {
			"description": "Job accepted",
			"content": {"application/json": {"example": {"job_id": "uuid", "status": "pending"}}},
		}
	},
)
async def extract_async_endpoint(
	payload: AsyncExtractRequest,
	background_tasks: BackgroundTasks,
	pdf_downloader=Depends(get_pdf_downloader),
	gemini_client=Depends(get_gemini_client),
):
	job_id = str(uuid.uuid4())
	repo = ExtractionJobRepository()
	repo.create_job(job_id, payload.case_id, payload.callback_url)

	service = get_extract_service(pdf_downloader=pdf_downloader, gemini_client=gemini_client)

	async def run_job():
		repo.mark_running(job_id)
		try:
			result = await service.extract(payload)
			repo.mark_success(job_id)
			if payload.callback_url:
				try:
					async with httpx.AsyncClient(timeout=10) as client:
						await client.post(payload.callback_url, json={
							"job_id": job_id,
							"case_id": payload.case_id,
							"status": "completed",
							"result": {
								"resume": result.resume,
								"timeline": [e.model_dump() for e in result.timeline],
								"evidence": [e.model_dump() for e in result.evidence],
							}
						})
				except Exception:
					pass
		except Exception as exc:  
			repo.mark_error(job_id, str(exc))
			if payload.callback_url:
				try:
					async with httpx.AsyncClient(timeout=10) as client:
						await client.post(payload.callback_url, json={
							"job_id": job_id,
							"case_id": payload.case_id,
							"status": "failed",
							"error": str(exc),
						})
				except Exception:
					pass

	background_tasks.add_task(run_job)
	return {"job_id": job_id, "status": "pending"}


@api_router.get(
	"/extract/jobs/{job_id}",
	dependencies=[Depends(require_api_key)],
	summary="Get extraction job status",
	description="Retrieve current status and metadata for a previously submitted asynchronous extraction job.",
	responses={
		200: {
			"description": "Job status",
			"content": {
				"application/json": {
					"example": {
						"id": "uuid",
						"case_id": "CASE12345",
						"status": "completed",
						"callback_url": "https://webhook.site/your-id",
						"error": None,
						"created_at": "2024-01-01T12:00:00Z",
						"updated_at": "2024-01-01T12:03:00Z"
					}
				}
			},
		},
		404: {"description": "Job not found"},
	},
)
async def get_job_status(job_id: str):
	repo = ExtractionJobRepository()
	job = repo.get(job_id)
	if not job:
		raise HTTPException(status_code=404, detail="Job not found")
	return job

