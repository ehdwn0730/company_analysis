from __future__ import annotations

import csv
from pathlib import Path

from company_job_analyzer.schema.job_posting_schema import JobUrlInput


def write_job_url_csv(items: list[JobUrlInput], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "job_title", "keyword", "url", "source"])
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "company": item.company,
                    "job_title": item.job_title or "",
                    "keyword": item.keyword or "",
                    "url": str(item.url),
                    "source": item.source or "",
                }
            )
    return path

