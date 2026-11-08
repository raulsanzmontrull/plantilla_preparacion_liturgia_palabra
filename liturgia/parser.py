"""Extracción de citas desde el HTML de leon-dufour.com."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional

from . import books
from .citations import dedupe_citations

SITE_CATEGORY_TO_OUTPUT = {
    "historicos": books.HISTORICOS,
    "profetas": books.PROFETAS,
    "epistolas": books.CARTAS,
    "cartas": books.CARTAS,
    "evangelios": books.EVANGELIOS,
}


@dataclass
class CitasPage:
    categories: Dict[str, List[str]] = field(default_factory=dict)
    raw_citations: List[str] = field(default_factory=list)


class _CitasExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.div_depth = 0
        self.panel_depth: Optional[int] = None
        self.data_citas: Optional[str] = None
        self.raw_citations: List[str] = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "div":
            if self.panel_depth is None and attributes.get("data-panel") == "citas":
                self.panel_depth = self.div_depth
            self.div_depth += 1

        if self.panel_depth is None:
            return

        if attributes.get("data-citas"):
            self.data_citas = attributes["data-citas"]
        if attributes.get("data-cita"):
            self.raw_citations.append(attributes["data-cita"])

    def handle_endtag(self, tag):
        if tag != "div":
            return
        self.div_depth -= 1
        if self.panel_depth is not None and self.div_depth == self.panel_depth:
            self.panel_depth = None


def parse_html(html: str) -> CitasPage:
    extractor = _CitasExtractor()
    extractor.feed(html)
    extractor.close()

    categories: Dict[str, List[str]] = {}
    if extractor.data_citas:
        try:
            payload = json.loads(extractor.data_citas)
        except (TypeError, ValueError):
            payload = None
        if isinstance(payload, dict):
            for key, values in payload.items():
                if isinstance(values, list):
                    categories[str(key)] = [str(value) for value in values]

    return CitasPage(
        categories=categories,
        raw_citations=extractor.raw_citations,
    )


def extract_citations(html: str) -> Dict[str, List[str]]:
    page = parse_html(html)
    result: Dict[str, List[str]] = {category: [] for category in books.CATEGORIES}

    if page.categories:
        for site_category, values in page.categories.items():
            output_category = SITE_CATEGORY_TO_OUTPUT.get(site_category)
            if output_category is None:
                continue
            result[output_category].extend(values)
    else:
        for citation in page.raw_citations:
            category = books.classify_citation(citation)
            if category is not None:
                result[category].append(citation)

    for category, citations in result.items():
        filtered = [
            citation
            for citation in citations
            if not books.is_excluded_citation(citation)
        ]
        result[category] = dedupe_citations(filtered)

    return result
