from __future__ import annotations

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base


class CaseORM(Base):
    __tablename__ = "cases"
    case_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    resume: Mapped[str] = mapped_column(Text)
    timelines: Mapped[list[TimelineEventORM]] = relationship(back_populates="case", cascade="all, delete-orphan")  # type: ignore
    evidences: Mapped[list[EvidenceORM]] = relationship(back_populates="case", cascade="all, delete-orphan")  # type: ignore


class TimelineEventORM(Base):
    __tablename__ = "timeline_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(Integer)
    event_name: Mapped[str] = mapped_column(String(255))
    event_description: Mapped[str] = mapped_column(Text)
    event_date: Mapped[str] = mapped_column(String(40))
    event_page_init: Mapped[int] = mapped_column(Integer)
    event_page_end: Mapped[int] = mapped_column(Integer)
    case: Mapped[CaseORM] = relationship(back_populates="timelines")  # type: ignore


class EvidenceORM(Base):
    __tablename__ = "evidences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.case_id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[int] = mapped_column(Integer)
    evidence_name: Mapped[str] = mapped_column(String(255))
    evidence_flaw: Mapped[str] = mapped_column(Text)
    evidence_page_init: Mapped[int] = mapped_column(Integer)
    evidence_page_end: Mapped[int] = mapped_column(Integer)
    case: Mapped[CaseORM] = relationship(back_populates="evidences")  # type: ignore


class ExtractionJobORM(Base):
    __tablename__ = "extraction_jobs"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    callback_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

__all__ = ["CaseORM", "TimelineEventORM", "EvidenceORM", "ExtractionJobORM"]
