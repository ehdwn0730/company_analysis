from __future__ import annotations

import time

import requests


class HtmlFetchError(RuntimeError):
    pass


def fetch_html(
    url: str,
    user_agent: str,
    timeout_sec: int = 15,
    retry_count: int = 2,
) -> str:
    headers = {"User-Agent": user_agent, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}
    last_error: Exception | None = None
    for attempt in range(retry_count + 1):
        try:
            response = requests.get(url, headers=headers, timeout=timeout_sec)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or response.encoding
            return response.text
        except Exception as exc:
            last_error = exc
            if attempt < retry_count:
                time.sleep(1.5 * (attempt + 1))
    raise HtmlFetchError(f"failed to fetch {url}: {last_error}") from last_error

