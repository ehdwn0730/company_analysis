from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from company_job_analyzer.schema.job_posting_schema import JobUrlInput


TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"fbclid", "gclid", "igshid", "ref", "source"}


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    query_pairs = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=False)
        if key not in TRACKING_PARAMS and not key.startswith(TRACKING_PREFIXES)
    ]
    query = urlencode(sorted(query_pairs), doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def deduplicate_job_urls(items: list[JobUrlInput]) -> list[JobUrlInput]:
    seen: set[str] = set()
    unique: list[JobUrlInput] = []
    for item in items:
        canonical = canonicalize_url(str(item.url))
        if canonical in seen:
            continue
        seen.add(canonical)
        unique.append(
            JobUrlInput(
                company=item.company,
                url=canonical,
                job_title=item.job_title,
                keyword=item.keyword,
                source=item.source,
            )
        )
    return unique

