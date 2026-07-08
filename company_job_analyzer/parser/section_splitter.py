from __future__ import annotations

from dataclasses import dataclass


REQUIREMENT_HEADERS = (
    "지원자격",
    "자격요건",
    "자격 조건",
    "필수요건",
    "필수 요건",
    "requirements",
    "qualification",
)
PREFERENCE_HEADERS = (
    "우대사항",
    "우대 조건",
    "우대조건",
    "preferred",
    "preference",
    "nice to have",
)
STOP_HEADERS = (
    "근무조건",
    "전형절차",
    "복리후생",
    "혜택",
    "채용절차",
    "접수기간",
    "제출서류",
    "기타사항",
)


@dataclass(frozen=True)
class SplitSections:
    requirements: str
    preferences: str
    other: str


def _is_header(line: str, headers: tuple[str, ...]) -> bool:
    lowered = line.lower().strip("[]【】() ")
    return any(header.lower() in lowered for header in headers)


def split_sections(text: str) -> SplitSections:
    current = "other"
    buckets = {"requirements": [], "preferences": [], "other": []}

    for line in text.splitlines():
        if _is_header(line, REQUIREMENT_HEADERS):
            current = "requirements"
            continue
        if _is_header(line, PREFERENCE_HEADERS):
            current = "preferences"
            continue
        if _is_header(line, STOP_HEADERS):
            current = "other"
        buckets[current].append(line)

    return SplitSections(
        requirements="\n".join(buckets["requirements"]).strip(),
        preferences="\n".join(buckets["preferences"]).strip(),
        other="\n".join(buckets["other"]).strip(),
    )

