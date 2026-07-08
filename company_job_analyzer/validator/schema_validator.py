from __future__ import annotations

from company_job_analyzer.schema.job_posting_schema import JobPosting


def validate_posting(posting: JobPosting) -> JobPosting:
    return JobPosting.model_validate(posting.model_dump())

