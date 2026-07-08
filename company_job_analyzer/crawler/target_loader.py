from __future__ import annotations

import csv
from pathlib import Path

from company_job_analyzer.crawler.auto_url_collector import SearchTarget


CSV_ENCODINGS = ("utf-8-sig", "utf-8", "cp949", "euc-kr")


def _read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    last_error: UnicodeDecodeError | None = None
    for encoding in CSV_ENCODINGS:
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader), list(reader.fieldnames or [])
        except UnicodeDecodeError as exc:
            last_error = exc
    raise UnicodeDecodeError(
        last_error.encoding if last_error else "unknown",
        last_error.object if last_error else b"",
        last_error.start if last_error else 0,
        last_error.end if last_error else 0,
        f"CSV encoding is not supported. Tried: {', '.join(CSV_ENCODINGS)}",
    )


def load_targets(path: Path) -> list[SearchTarget]:
    rows, fieldnames = _read_csv_rows(path)
    missing = {"company", "keyword"} - set(fieldnames)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")
    return [
        SearchTarget(company=(row.get("company") or "").strip(), keyword=(row.get("keyword") or "").strip())
        for row in rows
        if (row.get("company") or "").strip() and (row.get("keyword") or "").strip()
    ]


def parse_targets(companies: str, keywords: str) -> list[SearchTarget]:
    company_list = [value.strip() for value in companies.split(",") if value.strip()]
    keyword_list = [value.strip() for value in keywords.split(",") if value.strip()]
    return [SearchTarget(company=company, keyword=keyword) for company in company_list for keyword in keyword_list]
