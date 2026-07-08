from __future__ import annotations

import textwrap
from xml.sax.saxutils import escape

from company_job_analyzer.normalizer.item_summarizer import summarize_items
from company_job_analyzer.schema.job_posting_schema import ExtractedItem, RunReport


MAX_CHUNK_CHARS = 650
MAX_ITEMS_PER_CHUNK = 4
MAX_SINGLE_ITEM_CHARS = 500


def _split_long_text(text: str) -> list[str]:
    text = " ".join(text.split())
    if len(text) <= MAX_SINGLE_ITEM_CHARS:
        return [text]
    return textwrap.wrap(
        text,
        width=MAX_SINGLE_ITEM_CHARS,
        break_long_words=True,
        break_on_hyphens=False,
    )


def _item_lines(items: list[ExtractedItem]) -> list[str]:
    lines: list[str] = []
    for summary in summarize_items(items):
        parts = _split_long_text(summary)
        for index, part in enumerate(parts):
            prefix = "- " if index == 0 else "  "
            suffix = " (계속)" if index < len(parts) - 1 else ""
            lines.append(f"{prefix}{escape(part)}{suffix}")
    return lines or ["-"]


def _chunk_lines(lines: list[str]) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        if current and (
            len(current) >= MAX_ITEMS_PER_CHUNK
            or current_len + len(line) > MAX_CHUNK_CHARS
        ):
            chunks.append("<br/>".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += len(line)

    if current:
        chunks.append("<br/>".join(current))
    return chunks or ["-"]


def _items_chunks(items: list[ExtractedItem]) -> list[str]:
    return _chunk_lines(_item_lines(items))


def build_report_table_rows(report: RunReport) -> list[list[str]]:
    rows: list[list[str]] = [["회사 이름", "채용 직무", "주요업무", "자격요건", "우대사항"]]
    for posting in report.postings:
        main_task_chunks = _items_chunks(posting.main_tasks)
        requirement_chunks = _items_chunks(posting.requirements)
        preference_chunks = _items_chunks(posting.preferences)
        row_count = max(len(main_task_chunks), len(requirement_chunks), len(preference_chunks))

        for row_index in range(row_count):
            rows.append(
                [
                    escape(posting.company) if row_index == 0 else "",
                    escape(posting.job_title or "직무명 미상") if row_index == 0 else "(계속)",
                    main_task_chunks[row_index] if row_index < len(main_task_chunks) else "",
                    requirement_chunks[row_index] if row_index < len(requirement_chunks) else "",
                    preference_chunks[row_index] if row_index < len(preference_chunks) else "",
                ]
            )
    return rows
