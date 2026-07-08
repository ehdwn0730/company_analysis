from __future__ import annotations

from company_job_analyzer.schema.job_posting_schema import JobPosting


def quality_warnings(posting: JobPosting) -> list[str]:
    warnings: list[str] = []
    if not posting.main_tasks:
        warnings.append("주요업무 항목이 추출되지 않았습니다.")
    if not posting.requirements:
        warnings.append("자격요건 항목이 추출되지 않았습니다.")
    if not posting.preferences:
        warnings.append("우대사항 항목이 추출되지 않았습니다.")
    if len(posting.raw_text) < 300:
        warnings.append("본문 텍스트가 짧습니다. 동적 렌더링 페이지일 수 있습니다.")
    return warnings
