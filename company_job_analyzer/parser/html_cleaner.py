from __future__ import annotations

from bs4 import BeautifulSoup


def clean_html(html: str) -> BeautifulSoup:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "iframe", "svg"]):
        tag.decompose()
    for tag in soup.find_all(True):
        tag.attrs = {}
    return soup

