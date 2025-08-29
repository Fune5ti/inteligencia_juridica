from __future__ import annotations

from typing import Iterable
from sqlalchemy import delete
from sqlalchemy.orm import Session
from .db import get_session_factory
from .models import CaseORM, TimelineEventORM, EvidenceORM
from ..application.extraction_models import CaseExtraction


class CaseRepository:
    def __init__(self, session: Session | None = None):
        self._Session = get_session_factory()
        self._external_session = session

    def save_extraction(self, case_id: str, extraction: CaseExtraction) -> None:
        session = self._external_session or self._Session()
        close = self._external_session is None
        try:
            # Upsert case
            db_case = session.get(CaseORM, case_id)
            if db_case is None:
                db_case = CaseORM(case_id=case_id, resume=extraction.resume)
                session.add(db_case)
            else:
                db_case.resume = extraction.resume
            # Clear existing children
            session.execute(delete(TimelineEventORM).where(TimelineEventORM.case_id == case_id))
            session.execute(delete(EvidenceORM).where(EvidenceORM.case_id == case_id))
            # Insert new timeline events
            for ev in extraction.timeline:
                session.add(
                    TimelineEventORM(
                        case_id=case_id,
                        event_id=ev.event_id,
                        event_name=ev.event_name,
                        event_description=ev.event_description,
                        event_date=ev.event_date,
                        event_page_init=ev.event_page_init,
                        event_page_end=ev.event_page_end,
                    )
                )
            # Insert evidence
            for evd in extraction.evidence:
                session.add(
                    EvidenceORM(
                        case_id=case_id,
                        evidence_id=evd.evidence_id,
                        evidence_name=evd.evidence_name,
                        evidence_flaw=evd.evidence_flaw,
                        evidence_page_init=evd.evidence_page_init,
                        evidence_page_end=evd.evidence_page_end,
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            if close:
                session.close()

    def get_case(self, case_id: str) -> CaseExtraction | None:
        session = self._external_session or self._Session()
        close = self._external_session is None
        try:
            db_case = session.get(CaseORM, case_id)
            if not db_case:
                return None
            timeline = [
                {
                    "event_id": t.event_id,
                    "event_name": t.event_name,
                    "event_description": t.event_description,
                    "event_date": t.event_date,
                    "event_page_init": t.event_page_init,
                    "event_page_end": t.event_page_end,
                }
                for t in db_case.timelines
            ]
            evidence = [
                {
                    "evidence_id": e.evidence_id,
                    "evidence_name": e.evidence_name,
                    "evidence_flaw": e.evidence_flaw,
                    "evidence_page_init": e.evidence_page_init,
                    "evidence_page_end": e.evidence_page_end,
                }
                for e in db_case.evidences
            ]
            return CaseExtraction(resume=db_case.resume, timeline=timeline, evidence=evidence)  # type: ignore
        finally:
            if close:
                session.close()

__all__ = ["CaseRepository"]
