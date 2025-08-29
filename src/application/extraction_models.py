from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List


class Event(BaseModel):
    event_id: str = Field(min_length=1)
    event_name: str
    event_description: str
    event_date: str  # Keep string to avoid parsing complexities (expect ISO)
    event_page_init: int
    event_page_end: int


class Evidence(BaseModel):
    evidence_id: str = Field(min_length=1)
    evidence_name: str
    evidence_flaw: str
    evidence_page_init: int
    evidence_page_end: int


class CaseExtraction(BaseModel):
    resume: str
    timeline: List[Event]
    evidence: List[Evidence]


__all__ = [
    "Event",
    "Evidence",
    "CaseExtraction",
]