from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser


@lru_cache(maxsize=256)
def _parser_for(base_url: str) -> RobotFileParser:
    parser = RobotFileParser()
    parser.set_url(base_url.rstrip("/") + "/robots.txt")
    try:
        parser.read()
    except Exception:
        return parser
    return parser


def can_fetch(url: str, user_agent: str) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return False
    robots_url = f"{parsed.scheme}://{parsed.netloc}"
    parser = _parser_for(robots_url)
    try:
        return parser.can_fetch(user_agent, url)
    except Exception:
        return True

