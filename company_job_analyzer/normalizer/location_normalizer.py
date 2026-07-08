from __future__ import annotations

import re


KNOWN_LOCATIONS = ["서울", "경기", "인천", "부산", "대전", "대구", "광주", "울산", "세종", "제주", "판교", "분당"]


def normalize_locations(texts: list[str]) -> list[str]:
    corpus = "\n".join(texts)
    found = [location for location in KNOWN_LOCATIONS if re.search(location, corpus)]
    return sorted(set(found))

