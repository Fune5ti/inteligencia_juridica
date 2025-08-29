from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import get_session_factory
from .models import ExtractionJobORM
from datetime import datetime

class ExtractionJobRepository:
    def __init__(self, session: Session | None = None):
        self._Session = get_session_factory()
        self._external_session = session

    def _session(self):
        s = self._external_session or self._Session()
        return s, self._external_session is None

    def create_job(self, job_id: str, case_id: str, callback_url: str | None) -> None:
        s, close = self._session()
        try:
            job = ExtractionJobORM(id=job_id, case_id=case_id, status="pending", callback_url=callback_url)
            s.add(job)
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            if close:
                s.close()

    def mark_running(self, job_id: str):
        self._update_status(job_id, "running")

    def mark_success(self, job_id: str):
        self._update_status(job_id, "completed")

    def mark_error(self, job_id: str, message: str):
        self._update_status(job_id, "failed", message)

    def _update_status(self, job_id: str, status: str, error: str | None = None):
        s, close = self._session()
        try:
            job = s.get(ExtractionJobORM, job_id)
            if not job:
                return
            job.status = status
            job.error = error
            job.updated_at = datetime.utcnow()
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            if close:
                s.close()

    def get(self, job_id: str) -> dict | None:
        s, close = self._session()
        try:
            job = s.get(ExtractionJobORM, job_id)
            if not job:
                return None
            return {
                "id": job.id,
                "case_id": job.case_id,
                "status": job.status,
                "callback_url": job.callback_url,
                "error": job.error,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
            }
        finally:
            if close:
                s.close()

__all__ = ["ExtractionJobRepository"]
