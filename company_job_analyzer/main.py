from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from company_job_analyzer.config.settings import settings
from company_job_analyzer.crawler.auto_url_collector import collect_job_urls_from_search
from company_job_analyzer.crawler.html_fetcher import fetch_html
from company_job_analyzer.crawler.job_url_collector import collect_from_csv
from company_job_analyzer.crawler.robots_checker import can_fetch
from company_job_analyzer.crawler.target_loader import load_targets, parse_targets
from company_job_analyzer.crawler.url_deduplicator import deduplicate_job_urls
from company_job_analyzer.crawler.wanted_client import collect_wanted_job_urls, fetch_wanted_detail
from company_job_analyzer.extractor.llm_item_classifier import classify_items_with_fallback
from company_job_analyzer.extractor.main_task_extractor import extract_main_tasks
from company_job_analyzer.extractor.preference_extractor import extract_preferences
from company_job_analyzer.extractor.requirement_extractor import extract_requirements
from company_job_analyzer.messenger.kakao_sender import send_pdf_link_to_me
from company_job_analyzer.normalizer.career_normalizer import normalize_career_years
from company_job_analyzer.normalizer.education_normalizer import normalize_education
from company_job_analyzer.normalizer.location_normalizer import normalize_locations
from company_job_analyzer.normalizer.skill_normalizer import normalize_skills
from company_job_analyzer.parser.html_cleaner import clean_html
from company_job_analyzer.parser.section_splitter import split_sections
from company_job_analyzer.parser.text_extractor import extract_text
from company_job_analyzer.report.pdf_renderer import build_download_link, render_run_pdf
from company_job_analyzer.schema.job_posting_schema import JobPosting, JobUrlInput, NormalizedSummary, RunReport
from company_job_analyzer.storage.url_csv_writer import write_job_url_csv
from company_job_analyzer.validator.quality_checker import quality_warnings
from company_job_analyzer.validator.schema_validator import validate_posting

def setup_logging() -> None:
    settings.ensure_dirs()
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        handlers.append(logging.FileHandler(settings.log_dir / "run.log", encoding="utf-8"))
    except PermissionError:
        logging.getLogger("main").warning("Cannot write log file. Using console logging only.")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=handlers,
    )


def _build_posting_from_text(
    company: str,
    url: str,
    job_title: str | None,
    keyword: str | None,
    source: str | None,
    use_llm: bool,
    text: str,
    main_tasks_text: str | None = None,
    requirements_text: str | None = None,
    preferences_text: str | None = None,
) -> JobPosting:
    logger = logging.getLogger("analyze")
    if main_tasks_text is None or requirements_text is None or preferences_text is None:
        sections = split_sections(text)
        main_tasks_text = sections.main_tasks
        requirements_text = sections.requirements
        preferences_text = sections.preferences

    main_tasks = extract_main_tasks(main_tasks_text or "", text)
    requirements = extract_requirements(requirements_text or "", text)
    preferences = extract_preferences(preferences_text or "", text)
    if use_llm:
        requirements, preferences = classify_items_with_fallback(text, requirements, preferences)

    item_texts = [item.text for item in [*main_tasks, *requirements, *preferences]]
    posting = JobPosting(
        company=company,
        job_title=job_title,
        keyword=keyword,
        source=source,
        url=url,
        raw_text=text,
        main_tasks=main_tasks,
        requirements=requirements,
        preferences=preferences,
        normalized_summary=NormalizedSummary(
            skills=normalize_skills(item_texts),
            min_career_years=normalize_career_years(item_texts),
            education=normalize_education(item_texts),
            locations=normalize_locations([text]),
        ),
    )
    posting = validate_posting(posting)
    for warning in quality_warnings(posting):
        logger.warning("%s %s - %s", company, url, warning)
    return posting


def analyze_one(
    company: str,
    url: str,
    job_title: str | None,
    keyword: str | None,
    source: str | None,
    ignore_robots: bool,
    use_llm: bool,
) -> JobPosting:
    if source == "wanted":
        wanted_detail = fetch_wanted_detail(url)
        return _build_posting_from_text(
            company=wanted_detail.company or company,
            url=url,
            job_title=wanted_detail.job_title or job_title,
            keyword=keyword,
            source=source,
            use_llm=use_llm,
            text=wanted_detail.raw_text,
            main_tasks_text=wanted_detail.main_tasks_text,
            requirements_text=wanted_detail.requirements_text,
            preferences_text=wanted_detail.preferences_text,
        )

    if not ignore_robots and not can_fetch(url, settings.user_agent):
        raise PermissionError(f"robots.txt disallows fetching: {url}")

    html = fetch_html(
        url,
        user_agent=settings.user_agent,
        timeout_sec=settings.request_timeout_sec,
        retry_count=settings.request_retry_count,
    )
    text = extract_text(clean_html(html))
    return _build_posting_from_text(company, url, job_title, keyword, source, use_llm, text)


def collect_urls(
    targets_csv: Path | None,
    companies: str | None,
    keywords: str | None,
    site: str,
    limit_per_target: int | None,
    output_csv: Path,
) -> Path:
    if targets_csv:
        targets = load_targets(targets_csv)
    elif companies and keywords:
        targets = parse_targets(companies, keywords)
    else:
        raise ValueError("--collect-urls requires --targets-csv or both --companies and --keywords")

    collected = collect_job_urls_from_search(targets, site_name=site, limit_per_target=limit_per_target)
    write_job_url_csv(collected, output_csv)
    logging.getLogger("main").info("collected %d unique job URL(s) -> %s", len(collected), output_csv)
    return output_csv


def run_items(
    inputs: list[JobUrlInput],
    send_kakao: bool,
    ignore_robots: bool,
    limit: int | None,
    use_llm: bool,
) -> list[RunReport]:
    logger = logging.getLogger("main")
    inputs = deduplicate_job_urls(inputs)
    if limit:
        inputs = inputs[:limit]

    postings: list[JobPosting] = []
    failures: list[dict[str, str]] = []
    for item in inputs:
        try:
            logger.info("fetching %s - %s", item.company, item.url)
            posting = analyze_one(
                item.company,
                str(item.url),
                item.job_title,
                item.keyword,
                item.source,
                ignore_robots,
                use_llm,
            )
            postings.append(posting)
        except Exception as exc:
            logger.exception("failed %s %s", item.company, item.url)
            failures.append({"company": item.company, "url": str(item.url), "error": str(exc)})

    reports: list[RunReport] = []
    if postings:
        report = RunReport(title="원티드 데이터 사이언티스트 채용공고 분석 리포트", postings=postings)
        pdf_path = settings.output_dir / "wanted_data_scientist_report.pdf"

        render_run_pdf(report, pdf_path)
        report.pdf_path = str(pdf_path)
        report.download_link = build_download_link(pdf_path, settings.public_download_base_url)
        reports.append(report)

        if send_kakao:
            if not settings.kakao_access_token:
                logger.warning("KAKAO_ACCESS_TOKEN is missing. Skip Kakao send.")
            else:
                send_pdf_link_to_me(settings.kakao_access_token, report.title, report.download_link)
                logger.info("sent Kakao message for %s", report.title)

    if failures:
        logger.warning("%d URL(s) failed.", len(failures))
        for failure in failures:
            logger.warning("failed item: %s", json.dumps(failure, ensure_ascii=False))

    return reports


def run(
    input_csv: Path,
    send_kakao: bool,
    ignore_robots: bool,
    limit: int | None,
    use_llm: bool,
) -> list[RunReport]:
    return run_items(
        collect_from_csv(input_csv),
        send_kakao=send_kakao,
        ignore_robots=ignore_robots,
        limit=limit,
        use_llm=use_llm,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Company job posting analyzer")
    parser.add_argument("--input", default=None, help="Optional CSV with company,url,job_title,keyword. If omitted, Wanted data scientist list is analyzed.")
    parser.add_argument("--collect-urls", action="store_true", help="Collect job URLs before analysis")
    parser.add_argument("--targets-csv", default=None, help="CSV with company,keyword for automatic URL collection")
    parser.add_argument("--companies", default=None, help="Comma-separated company names for URL collection")
    parser.add_argument("--keywords", default=None, help="Comma-separated job keywords for URL collection")
    parser.add_argument("--site", default="generic", help="Site config name in config/sites.yaml")
    parser.add_argument("--collected-output", default=str(settings.data_dir / "collected_job_urls.csv"), help="Output CSV for collected URLs")
    parser.add_argument("--send-kakao", action="store_true", help="Send generated PDF links to KakaoTalk myself")
    parser.add_argument("--ignore-robots", action="store_true", help="Skip robots.txt check for manually permitted pages")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM-based requirement/preference classification with rule fallback")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of URLs for smoke tests")
    parser.add_argument("--collect-only", action="store_true", help="Only collect URL CSV and skip analysis")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()

    if args.collect_urls:
        input_csv = collect_urls(
            targets_csv=Path(args.targets_csv) if args.targets_csv else None,
            companies=args.companies,
            keywords=args.keywords,
            site=args.site,
            limit_per_target=args.limit,
            output_csv=Path(args.collected_output),
        )
        if args.collect_only:
            return
    elif args.input:
        input_csv = Path(args.input)
    else:
        wanted_inputs = collect_wanted_job_urls(settings.wanted_list_url, max_items=args.limit)
        reports = run_items(
            wanted_inputs,
            send_kakao=args.send_kakao or settings.send_kakao,
            ignore_robots=True,
            limit=None,
            use_llm=args.use_llm,
        )
        for report in reports:
            logging.getLogger("main").info("generated %s -> %s", report.title, report.download_link)
        return

    reports = run(
        input_csv,
        send_kakao=args.send_kakao or settings.send_kakao,
        ignore_robots=args.ignore_robots,
        limit=args.limit,
        use_llm=args.use_llm,
    )
    for report in reports:
        logging.getLogger("main").info("generated %s -> %s", report.title, report.download_link)


if __name__ == "__main__":
    main()
