from __future__ import annotations

import re


def normalize_career_years(texts: list[str]) -> int | None:
    corpus = "\n".join(texts)
    matches = re.findall(r"(\d+)\s*년\s*(?:이상|차|경력)?", corpus)
    if not matches:
        return None
    return min(int(value) for value in matches)

