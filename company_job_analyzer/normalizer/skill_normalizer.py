from __future__ import annotations

import re


SKILL_ALIASES = {
    "python": "Python",
    "파이썬": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "react": "React",
    "vue": "Vue",
    "sql": "SQL",
    "aws": "AWS",
    "gcp": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "spring": "Spring",
    "django": "Django",
    "fastapi": "FastAPI",
}


def normalize_skills(texts: list[str]) -> list[str]:
    found: set[str] = set()
    corpus = "\n".join(texts).lower()
    for alias, canonical in SKILL_ALIASES.items():
        if re.search(rf"(?<![a-z0-9]){re.escape(alias.lower())}(?![a-z0-9])", corpus):
            found.add(canonical)
    return sorted(found)

