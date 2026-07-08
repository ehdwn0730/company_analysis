from __future__ import annotations


EDUCATION_KEYWORDS = ["고졸", "초대졸", "전문학사", "학사", "석사", "박사", "대졸"]


def normalize_education(texts: list[str]) -> str | None:
    corpus = "\n".join(texts)
    for keyword in EDUCATION_KEYWORDS:
        if keyword in corpus:
            return keyword
    return None

