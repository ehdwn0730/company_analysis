from __future__ import annotations

import re

from company_job_analyzer.extractor.evidence_mapper import map_evidence
from company_job_analyzer.schema.job_posting_schema import ExtractedItem, ItemCategory


def _candidate_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"^[\-ㆍ•*\d.)\s]+", "", raw).strip()
        if 3 <= len(line) <= 220:
            lines.append(line)
    return lines


def extract_requirements(section_text: str, full_text: str) -> list[ExtractedItem]:
    items: list[ExtractedItem] = []
    for line in _candidate_lines(section_text):
        items.append(
            ExtractedItem(
                category=ItemCategory.REQUIREMENT,
                text=line,
                evidence_sentence=map_evidence(line, full_text),
                confidence=0.78,
            )
        )
    return items

