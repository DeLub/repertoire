"""HTML parsing for musicalifeiten.nl content."""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import Optional


class MusicaliefeitenParser(HTMLParser):
    """Parser for musicalifeiten.nl HTML content."""

    def __init__(self):
        super().__init__()
        self.paragraphs: list[str] = []
        self.current_text: list[str] = []
        self.in_article = False
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Handle HTML start tags."""
        if tag in ("script", "style"):
            self.in_script = tag == "script"
            self.in_style = tag == "style"
        elif tag == "article":
            self.in_article = True
        elif tag in ("p", "div"):
            if self.current_text:
                text = " ".join(self.current_text).strip()
                if text:
                    self.paragraphs.append(text)
                self.current_text = []

    def handle_endtag(self, tag: str) -> None:
        """Handle HTML end tags."""
        if tag in ("script", "style"):
            self.in_script = False
            self.in_style = False
        elif tag == "article":
            self.in_article = False
        elif tag in ("p", "div"):
            if self.current_text:
                text = " ".join(self.current_text).strip()
                if text:
                    self.paragraphs.append(text)
                self.current_text = []

    def handle_data(self, data: str) -> None:
        """Handle text data."""
        if not self.in_script and not self.in_style and self.in_article:
            cleaned = data.strip()
            if cleaned:
                self.current_text.append(cleaned)

    def get_paragraphs(self) -> list[str]:
        """Get all extracted paragraphs."""
        if self.current_text:
            text = " ".join(self.current_text).strip()
            if text:
                self.paragraphs.append(text)
        return [p for p in self.paragraphs if len(p) > 10]


def extract_text_from_html(html: str) -> list[str]:
    """Extract paragraphs from HTML content."""
    parser = MusicaliefeitenParser()
    try:
        parser.feed(html)
    except Exception:
        # If parsing fails, return empty list
        return []
    return parser.get_paragraphs()


def clean_text(text: str) -> str:
    """Clean text of extra whitespace and formatting."""
    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)
    # Remove common HTML entities
    text = text.replace("&nbsp;", " ")
    text = text.replace("&quot;", '"')
    text = text.replace("&amp;", "&")
    return text.strip()
