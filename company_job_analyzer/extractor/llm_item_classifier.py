from __future__ import annotations

import json
import logging
from typing import Any

import requests

from company_job_analyzer.config.settings import settings
from company_job_analyzer.schema.job_posting_schema import ExtractedItem, ItemCategory


SYSTEM_PROMPT = """You classify Korean job posting text.
Return only valid JSON with this exact shape:
{
  "requirements": [
    {"text": "...", "evidence_sentence": "...", "confidence": 0.0}
  ],
  "preferences": [
    {"text": "...", "evidence_sentence": "...", "confidence": 0.0}
  ]
}
Rules:
- requirements means mandatory qualifications, minimum experience, required skills, education, location, certificates.
- preferences means nice-to-have, preferred experience, bonus skills, 우대사항.
- evidence_sentence must be copied from the source text as a short supporting sentence.
- Keep each item atomic.
- Do not invent facts.
"""


def _extract_json_object(content: str) -> dict[str, Any]:
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.removeprefix("json").strip()
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response did not contain a JSON object")
    return json.loads(content[start : end + 1])


def classify_items_with_llm(text: str) -> tuple[list[ExtractedItem], list[ExtractedItem]]:
    if not settings.llm_api_key:
        raise RuntimeError("OPENAI_API_KEY or LLM_API_KEY is required for LLM classification")

    clipped_text = text[:12000]
    payload = {
        "model": settings.llm_model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": clipped_text},
        ],
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        settings.llm_endpoint,
        headers={
            "Authorization": f"Bearer {settings.llm_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=settings.llm_timeout_sec,
    )
    response.raise_for_status()
    raw = response.json()
    content = raw["choices"][0]["message"]["content"]
    parsed = _extract_json_object(content)

    requirements = [
        ExtractedItem(
            category=ItemCategory.REQUIREMENT,
            text=str(item.get("text", "")).strip(),
            evidence_sentence=str(item.get("evidence_sentence") or item.get("text") or "").strip(),
            confidence=float(item.get("confidence", 0.8)),
            extractor="llm",
        )
        for item in parsed.get("requirements", [])
        if str(item.get("text", "")).strip()
    ]
    preferences = [
        ExtractedItem(
            category=ItemCategory.PREFERENCE,
            text=str(item.get("text", "")).strip(),
            evidence_sentence=str(item.get("evidence_sentence") or item.get("text") or "").strip(),
            confidence=float(item.get("confidence", 0.8)),
            extractor="llm",
        )
        for item in parsed.get("preferences", [])
        if str(item.get("text", "")).strip()
    ]
    return requirements, preferences


def classify_items_with_fallback(
    text: str,
    rule_requirements: list[ExtractedItem],
    rule_preferences: list[ExtractedItem],
) -> tuple[list[ExtractedItem], list[ExtractedItem]]:
    try:
        return classify_items_with_llm(text)
    except Exception as exc:
        logging.getLogger("llm_item_classifier").warning("LLM classification failed. Falling back to rules: %s", exc)
        return rule_requirements, rule_preferences

