from __future__ import annotations

from company_job_analyzer.parser.text_extractor import split_sentences


def map_evidence(item_text: str, source_text: str) -> str:
    normalized_item = item_text.lower().strip()
    for sentence in split_sentences(source_text):
        if normalized_item and normalized_item in sentence.lower():
            return sentence
    return item_text

