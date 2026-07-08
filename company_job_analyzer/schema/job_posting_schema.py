from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class ItemCategory(str, Enum):
    REQUIREMENT = "requirement"
    PREFERENCE = "preference"


class JobUrlInput(BaseModel):
    company: str = Field(min_length=1)
    url: HttpUrl
    job_title: str | None = None
    keyword: str | None = None
    source: str | None = None


class ExtractedItem(BaseModel):
    category: ItemCategory
    text: str = Field(min_length=1)
    normalized: str | None = None
    evidence_sentence: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    extractor: str = "rule"


class NormalizedSummary(BaseModel):
    skills: list[str] = Field(default_factory=list)
    min_career_years: int | None = None
    education: str | None = None
    locations: list[str] = Field(default_factory=list)


class JobPosting(BaseModel):
    company: str
    job_title: str | None = None
    keyword: str | None = None
    source: str | None = None
    url: HttpUrl
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_text: str
    requirements: list[ExtractedItem] = Field(default_factory=list)
    preferences: list[ExtractedItem] = Field(default_factory=list)
    normalized_summary: NormalizedSummary = Field(default_factory=NormalizedSummary)


class CompanyReport(BaseModel):
    company: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    postings: list[JobPosting] = Field(default_factory=list)
    pdf_path: str | None = None
    download_link: str | None = None
