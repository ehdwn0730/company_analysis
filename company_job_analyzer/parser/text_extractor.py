from __future__ import annotations

import re

from bs4 import BeautifulSoup


def extract_text(soup: BeautifulSoup) -> str:
    for br in soup.find_all("br"):
        br.replace_with("\n")
    text = soup.get_text("\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def split_sentences(text: str) -> list[str]:
    candidates: list[str] = []
    for line in text.splitlines():
        line = line.strip(" -ㆍ•\t")
        if not line:
            continue
        parts = re.split(r"(?<=[.!?。])\s+", line)
        candidates.extend(part.strip() for part in parts if part.strip())
    return candidates

