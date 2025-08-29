from __future__ import annotations

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.models import Base  # type: ignore
from src.infrastructure.case_repository import CaseRepository
from src.application.extraction_models import CaseExtraction, Event, Evidence


@pytest.fixture()
def session():
    # Use SQLite in-memory for speed & isolation
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    with SessionLocal() as s:
        yield s


def make_extraction(resume: str, ev_suffix: str, evid_suffix: str) -> CaseExtraction:
    timeline = [
        Event(
            event_id=1,
            event_name=f"EventA{ev_suffix}",
            event_description=f"DescA{ev_suffix}",
            event_date="2024-01-01",
            event_page_init=1,
            event_page_end=2,
        ),
        Event(
            event_id=2,
            event_name=f"EventB{ev_suffix}",
            event_description=f"DescB{ev_suffix}",
            event_date="2024-01-02",
            event_page_init=3,
            event_page_end=4,
        ),
    ]
    evidence = [
        Evidence(
            evidence_id=1,
            evidence_name=f"EvidenceA{evid_suffix}",
            evidence_flaw=f"FlawA{evid_suffix}",
            evidence_page_init=10,
            evidence_page_end=11,
        )
    ]
    return CaseExtraction(resume=resume, timeline=timeline, evidence=evidence)


def test_upsert_replaces_children(session):
    repo = CaseRepository(session=session)
    case_id = "CASE123"

    first = make_extraction("Resume v1", "_v1", "_v1")
    repo.save_extraction(case_id, first)

    stored1 = repo.get_case(case_id)
    assert stored1 is not None
    assert stored1.resume == "Resume v1"
    assert len(stored1.timeline) == 2
    assert stored1.timeline[0].event_name.endswith("_v1")
    assert stored1.evidence[0].evidence_name.endswith("_v1")

    second = make_extraction("Resume v2", "_v2", "_v2")
    repo.save_extraction(case_id, second)

    stored2 = repo.get_case(case_id)
    assert stored2 is not None
    assert stored2.resume == "Resume v2"
    # Ensure children fully replaced (not appended)
    assert len(stored2.timeline) == 2
    assert stored2.timeline[0].event_name.endswith("_v2")
    assert stored2.evidence[0].evidence_name.endswith("_v2")

    # No leftover old records
    names = {t.event_name for t in stored2.timeline}
    assert all(name.endswith("_v2") for name in names)
