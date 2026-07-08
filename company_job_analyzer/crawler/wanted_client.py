from __future__ import annotations

import logging
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

import requests

from company_job_analyzer.config.settings import settings
from company_job_analyzer.parser.html_cleaner import clean_html
from company_job_analyzer.parser.text_extractor import extract_text
from company_job_analyzer.schema.job_posting_schema import JobUrlInput


WANTED_BASE_URL = "https://www.wanted.co.kr"
WANTED_LIST_API = f"{WANTED_BASE_URL}/api/chaos/navigation/v1/results"
WANTED_DETAIL_API = f"{WANTED_BASE_URL}/api/chaos/jobs/v1/positions"


@dataclass(frozen=True)
class WantedDetail:
    company: str
    job_title: str
    url: str
    raw_text: str
    main_tasks_text: str
    requirements_text: str
    preferences_text: str


def _headers(referer: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": settings.user_agent,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Origin": WANTED_BASE_URL,
    }
    if referer:
        headers["Referer"] = referer
    return headers


def _list_api_params(list_url: str, limit: int, offset: int) -> dict[str, str | int]:
    parsed = urlsplit(list_url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 3 or parts[0] != "wdlist":
        raise ValueError(f"Not a Wanted wdlist URL: {list_url}")

    query = {key: values[-1] for key, values in parse_qs(parsed.query).items()}
    params: dict[str, str | int] = {
        "job_group_id": parts[1],
        "job_ids": parts[2],
        "country": query.get("country", "kr"),
        "job_sort": query.get("job_sort", "job.popularity_order"),
        "years": query.get("years", "-1"),
        "locations": query.get("locations", "all"),
        "limit": limit,
        "offset": offset,
    }
    return params


def _iter_dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_dicts(child)


def _first_string(value: Any, keys: tuple[str, ...]) -> str | None:
    lowered_keys = tuple(key.lower() for key in keys)
    for item in _iter_dicts(value):
        for key, child in item.items():
            if key.lower() in lowered_keys and isinstance(child, str) and child.strip():
                return child.strip()
    return None


def _company_name(value: Any) -> str | None:
    for item in _iter_dicts(value):
        company = item.get("company")
        if isinstance(company, dict):
            name = company.get("name") or company.get("company_name")
            if isinstance(name, str) and name.strip():
                return name.strip()
        if isinstance(company, str) and company.strip():
            return company.strip()
        for key in ("company_name", "companyName"):
            if isinstance(item.get(key), str) and item[key].strip():
                return item[key].strip()
    return None


def _extract_position_cards(payload: Any) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    seen: set[int] = set()
    for item in _iter_dicts(payload):
        job_id = item.get("id") or item.get("job_id") or item.get("position_id")
        if not isinstance(job_id, int) or job_id in seen:
            continue
        title = item.get("position") or item.get("title") or item.get("job_title")
        if not isinstance(title, str):
            continue
        cards.append(item)
        seen.add(job_id)
    return cards


def collect_wanted_job_urls(list_url: str, page_size: int = 100, max_items: int | None = None) -> list[JobUrlInput]:
    logger = logging.getLogger("wanted_client")
    collected: list[JobUrlInput] = []
    offset = 0

    while True:
        params = _list_api_params(list_url, limit=page_size, offset=offset)
        response = requests.get(
            WANTED_LIST_API,
            params=params,
            headers=_headers(referer=list_url),
            timeout=settings.request_timeout_sec,
        )
        response.raise_for_status()
        payload = response.json()
        cards = _extract_position_cards(payload)
        if not cards:
            break

        for card in cards:
            job_id = int(card.get("id") or card.get("job_id") or card.get("position_id"))
            title = str(card.get("position") or card.get("title") or card.get("job_title") or "").strip() or None
            company = _company_name(card) or "원티드"
            collected.append(
                JobUrlInput(
                    company=company,
                    job_title=title,
                    keyword="데이터 사이언티스트",
                    url=f"{WANTED_BASE_URL}/wd/{job_id}",
                    source="wanted",
                )
            )
            if max_items and len(collected) >= max_items:
                logger.info("wanted collection reached max_items=%d", max_items)
                return collected

        if len(cards) < page_size:
            break
        offset += page_size

    logger.info("collected %d Wanted job URL(s)", len(collected))
    return collected


def wanted_job_id_from_url(url: str) -> int:
    match = re.search(r"/wd/(\d+)", url)
    if not match:
        raise ValueError(f"Not a Wanted job detail URL: {url}")
    return int(match.group(1))


def _collect_strings_by_key(value: Any, key_patterns: tuple[str, ...]) -> list[str]:
    results: list[str] = []
    for item in _iter_dicts(value):
        for key, child in item.items():
            lowered = key.lower()
            if not any(pattern in lowered for pattern in key_patterns):
                continue
            if isinstance(child, str) and child.strip():
                results.append(child.strip())
            elif isinstance(child, list):
                results.extend(str(part).strip() for part in child if str(part).strip())
    return results


def _collect_all_strings(value: Any, limit: int = 80) -> list[str]:
    strings: list[str] = []
    if isinstance(value, dict):
        for child in value.values():
            strings.extend(_collect_all_strings(child, limit=limit))
            if len(strings) >= limit:
                break
    elif isinstance(value, list):
        for child in value:
            strings.extend(_collect_all_strings(child, limit=limit))
            if len(strings) >= limit:
                break
    elif isinstance(value, str) and value.strip():
        strings.append(value.strip())
    return strings[:limit]


def _plain_text(value: str) -> str:
    if "<" in value and ">" in value:
        return extract_text(clean_html(value))
    return value.strip()


def _detail_to_wanted_detail(payload: Any, url: str) -> WantedDetail:
    company = _company_name(payload) or "원티드"
    title = _first_string(payload, ("position", "title", "job_title")) or "직무명 미상"
    main_tasks = _collect_strings_by_key(payload, ("responsib", "main_task", "main_tasks", "task"))
    requirements = _collect_strings_by_key(payload, ("require", "qualification", "qualifications"))
    preferences = _collect_strings_by_key(payload, ("preferred", "preference"))

    raw_parts = _collect_all_strings(payload)
    raw_text = "\n".join(dict.fromkeys(_plain_text(part) for part in raw_parts if _plain_text(part)))
    main_tasks_text = "\n".join(dict.fromkeys(_plain_text(part) for part in main_tasks if _plain_text(part)))
    requirements_text = "\n".join(dict.fromkeys(_plain_text(part) for part in requirements if _plain_text(part)))
    preferences_text = "\n".join(dict.fromkeys(_plain_text(part) for part in preferences if _plain_text(part)))
    if not requirements_text and raw_text:
        requirements_text = raw_text

    return WantedDetail(
        company=company,
        job_title=title,
        url=url,
        raw_text=raw_text,
        main_tasks_text=main_tasks_text,
        requirements_text=requirements_text,
        preferences_text=preferences_text,
    )


def _detail_from_html(html: str, url: str) -> WantedDetail:
    job_posting: dict[str, Any] = {}
    for script in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, flags=re.DOTALL):
        try:
            data = json.loads(script)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            job_posting = data
            break

    title = str(job_posting.get("title") or "직무명 미상").strip()
    hiring_org = job_posting.get("hiringOrganization") or {}
    company = str(hiring_org.get("name") or "원티드").strip()
    description = str(job_posting.get("description") or "").strip()

    plain_html_text = extract_text(clean_html(html))
    embedded_main_tasks = _embedded_json_string(html, "main_tasks")
    embedded_requirements = _embedded_json_string(html, "requirements")
    embedded_preferences = _embedded_json_string(html, "preferred_points")
    main_tasks_match = re.search(r"(?:주요업무|주요 업무|담당업무|담당 업무|responsibilities)\s*(.*?)(?:자격요건|지원자격|requirements?|우대사항|preferred)", plain_html_text, re.IGNORECASE | re.DOTALL)
    requirements_match = re.search(r"(?:자격요건|지원자격|requirements?)\s*(.*?)(?:우대사항|preferred|혜택|복지|채용절차)", plain_html_text, re.IGNORECASE | re.DOTALL)
    preferences_match = re.search(r"(?:우대사항|우대조건|preferred)\s*(.*?)(?:혜택|복지|채용절차|마감일|기타)", plain_html_text, re.IGNORECASE | re.DOTALL)

    main_tasks_text = embedded_main_tasks or (main_tasks_match.group(1).strip() if main_tasks_match else description)
    requirements_text = embedded_requirements or (requirements_match.group(1).strip() if requirements_match else "")
    preferences_text = embedded_preferences or (preferences_match.group(1).strip() if preferences_match else "")
    raw_text = "\n".join(part for part in [title, company, description, plain_html_text] if part)

    return WantedDetail(
        company=company,
        job_title=title,
        url=url,
        raw_text=raw_text,
        main_tasks_text=main_tasks_text,
        requirements_text=requirements_text,
        preferences_text=preferences_text,
    )


def _embedded_json_string(html: str, key: str) -> str:
    match = re.search(rf'"{re.escape(key)}":"((?:\\.|[^"\\])*)"', html)
    if not match:
        return ""
    try:
        return _plain_text(json.loads(f'"{match.group(1)}"'))
    except json.JSONDecodeError:
        return ""


def fetch_wanted_detail(url: str) -> WantedDetail:
    job_id = wanted_job_id_from_url(url)
    api_url = f"{WANTED_DETAIL_API}/{job_id}"
    response = requests.get(api_url, headers=_headers(referer=url), timeout=settings.request_timeout_sec)
    if response.status_code < 400:
        return _detail_to_wanted_detail(response.json(), url)

    html_response = requests.get(url, headers=_headers(referer=url), timeout=settings.request_timeout_sec)
    html_response.raise_for_status()
    html_response.encoding = "utf-8"
    return _detail_from_html(html_response.text, url)


def wanted_list_api_url(list_url: str, limit: int = 100, offset: int = 0) -> str:
    params = _list_api_params(list_url, limit=limit, offset=offset)
    return f"{WANTED_LIST_API}?{urlencode(params)}"
