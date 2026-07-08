from __future__ import annotations

import csv
from pathlib import Path

from company_job_analyzer.schema.job_posting_schema import JobUrlInput


REQUIRED_COLUMNS = {"company", "url"}
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


def collect_from_csv(path: Path) -> list[JobUrlInput]:
    rows, fieldnames = _read_csv_rows(path)
    missing = REQUIRED_COLUMNS - set(fieldnames)
    if missing:
        raise ValueError(f"CSV missing required columns: {', '.join(sorted(missing))}")
    return [
        JobUrlInput(
            company=(row.get("company") or "").strip(),
            url=(row.get("url") or "").strip(),
            job_title=(row.get("job_title") or "").strip() or None,
            keyword=(row.get("keyword") or "").strip() or None,
            source=(row.get("source") or "").strip() or "manual",
        )
        for row in rows
        if (row.get("company") or "").strip() and (row.get("url") or "").strip()
    ]
