from __future__ import annotations

import re

from company_job_analyzer.schema.job_posting_schema import ExtractedItem


MAX_SUMMARY_ITEMS = 5
MAX_SUMMARY_CHARS = 90

LEADING_VERBS = (
    "create",
    "curate",
    "engage",
    "build",
    "collaborate",
    "contribute",
    "shape",
    "develop",
    "design",
    "analyze",
    "manage",
    "operate",
    "lead",
    "support",
)

PHRASE_REPLACEMENTS = {
    "high-quality": "quality",
    "technical content": "tech content",
    "developer community": "dev community",
    "machine learning": "ML",
    "artificial intelligence": "AI",
    "large language model": "LLM",
    "large language models": "LLMs",
    "experience with": "exp. in",
    "experience building": "building exp.",
    "proven track record of": "track record in",
    "ability to": "can",
    "understanding of": "understands",
}


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" -ㆍ•*\t\r\n")


def _drop_parenthetical_noise(text: str) -> str:
    return re.sub(r"\s*\([^)]{20,}\)", "", text)


def _compress_phrases(text: str) -> str:
    compressed = text
    for source, target in PHRASE_REPLACEMENTS.items():
        compressed = re.sub(re.escape(source), target, compressed, flags=re.IGNORECASE)
    return compressed


def _cut_at_soft_boundary(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    candidate = text[:max_chars]
    for boundary in [", ", " and ", " to ", " for ", " with ", " 및 ", "과 ", "와 "]:
        index = candidate.rfind(boundary)
        if index >= max_chars * 0.45:
            candidate = candidate[:index]
            break
    return candidate.rstrip(" ,.;:") + "..."


def summarize_sentence(text: str, max_chars: int = MAX_SUMMARY_CHARS) -> str:
    summary = _normalize_space(text)
    summary = _drop_parenthetical_noise(summary)
    summary = _compress_phrases(summary)
    summary = re.sub(r"^(responsible for|you will|you are expected to)\s+", "", summary, flags=re.IGNORECASE)

    lowered = summary.lower()
    for verb in LEADING_VERBS:
        marker = f"{verb} "
        if marker in lowered:
            summary = summary[lowered.find(marker) :]
            break

    return _cut_at_soft_boundary(summary, max_chars)


def summarize_items(items: list[ExtractedItem], max_items: int = MAX_SUMMARY_ITEMS) -> list[str]:
    summaries: list[str] = []
    seen: set[str] = set()

    for item in items:
        summary = summarize_sentence(item.text)
        key = summary.lower()
        if not summary or key in seen:
            continue
        summaries.append(summary)
        seen.add(key)
        if len(summaries) >= max_items:
            break

    return summaries or ["-"]
