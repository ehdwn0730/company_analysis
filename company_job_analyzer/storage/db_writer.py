from __future__ import annotations

from company_job_analyzer.schema.job_posting_schema import RunReport


def write_to_db(_report: RunReport) -> None:
    """Reserved extension point for a future sqlite or SQLAlchemy writer."""
    return None
