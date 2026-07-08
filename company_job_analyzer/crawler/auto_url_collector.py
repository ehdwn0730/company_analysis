from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from urllib.parse import parse_qs, quote_plus, urljoin, urlsplit

import requests
import yaml
from bs4 import BeautifulSoup

from company_job_analyzer.config.settings import settings
from company_job_analyzer.crawler.url_deduplicator import deduplicate_job_urls
from company_job_analyzer.schema.job_posting_schema import JobUrlInput


@dataclass(frozen=True)
class SearchTarget:
    company: str
    keyword: str


def load_site_configs() -> dict:
    if not settings.sites_yaml.exists():
        return {}
    with settings.sites_yaml.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _unwrap_search_href(href: str) -> str:
    parts = urlsplit(href)
    if "google." in parts.netloc and parts.path == "/url":
        target = parse_qs(parts.query).get("q", [""])[0]
        if target:
            return target
    return href


def collect_job_urls_from_search(
    targets: list[SearchTarget],
    site_name: str = "generic",
    limit_per_target: int | None = None,
) -> list[JobUrlInput]:
    logger = logging.getLogger("auto_url_collector")
    configs = load_site_configs()
    site_config = (configs.get("sites") or {}).get(site_name, {})
    templates = site_config.get("search_url_templates") or []
    include_patterns = [p.lower() for p in site_config.get("job_link_patterns", [])]
    exclude_patterns = [p.lower() for p in site_config.get("exclude_link_patterns", [])]
    limit = limit_per_target or settings.search_result_limit
    collected: list[JobUrlInput] = []

    for target in targets:
        target_count = 0
        for template in templates:
            if target_count >= limit:
                break
            search_url = template.format(
                company=quote_plus(target.company),
                keyword=quote_plus(target.keyword),
            )
            try:
                response = requests.get(
                    search_url,
                    headers={"User-Agent": settings.user_agent},
                    timeout=settings.request_timeout_sec,
                )
                response.raise_for_status()
            except Exception as exc:
                logger.warning("search failed company=%s keyword=%s url=%s error=%s", target.company, target.keyword, search_url, exc)
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            for anchor in soup.find_all("a", href=True):
                href = _unwrap_search_href(urljoin(search_url, anchor["href"]))
                href_lower = href.lower()
                if exclude_patterns and any(pattern in href_lower for pattern in exclude_patterns):
                    continue
                if include_patterns and not any(pattern in href_lower for pattern in include_patterns):
                    continue
                try:
                    collected.append(
                        JobUrlInput(
                            company=target.company,
                            keyword=target.keyword,
                            url=href,
                            job_title=(anchor.get_text(" ", strip=True) or None),
                            source=site_name,
                        )
                    )
                    target_count += 1
                except Exception:
                    continue
                if target_count >= limit:
                    break
            time.sleep(float((configs.get("default") or {}).get("request_interval_sec", 1.0)))

    return deduplicate_job_urls(collected)
