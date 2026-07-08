from __future__ import annotations

from xml.sax.saxutils import escape

from company_job_analyzer.schema.job_posting_schema import CompanyReport, ExtractedItem


def bullet_lines(items: list[ExtractedItem]) -> str:
    if not items:
        return "- 추출된 항목 없음"
    return "<br/><br/>".join(
        f"- {escape(item.text)}<br/><font size='8'>근거: {escape(item.evidence_sentence)}</font>"
        for item in items
    )


def build_pdf_story_html(report: CompanyReport) -> list[tuple[str, str]]:
    story: list[tuple[str, str]] = [("title", f"{escape(report.company)} 채용공고 분석 리포트")]
    for posting in report.postings:
        story.append(("heading", escape(posting.job_title or "직무명 미상")))
        story.append(("meta", f"URL: {escape(str(posting.url))}"))
        summary = posting.normalized_summary
        story.append(("body", f"기술스택: {escape(', '.join(summary.skills) or '-')}"))
        story.append(("body", f"최소 경력: {summary.min_career_years if summary.min_career_years is not None else '-'}"))
        story.append(("body", f"학력: {escape(summary.education or '-')}"))
        story.append(("body", f"지역: {escape(', '.join(summary.locations) or '-')}"))
        story.append(("subheading", "지원자격"))
        story.append(("html", bullet_lines(posting.requirements)))
        story.append(("subheading", "우대조건"))
        story.append(("html", bullet_lines(posting.preferences)))
    return story
