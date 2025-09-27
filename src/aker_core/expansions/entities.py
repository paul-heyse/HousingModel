"""Entity extraction utilities for expansion announcements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

try:  # pragma: no cover - optional dependency
    import spacy
    from spacy.language import Language
except Exception:  # pragma: no cover - graceful fallback
    spacy = None
    Language = None  # type: ignore


@dataclass(frozen=True)
class EntityExtractionResult:
    company: Optional[str]
    company_confidence: float
    location: Dict[str, Optional[str]]
    location_confidence: float
    industry: Optional[str]
    industry_confidence: float


class EntityExtractor:
    """Rule-based entity extractor with optional spaCy support."""

    def __init__(self, enable_spacy: bool = True) -> None:
        self._nlp: Optional[Language] = None
        if enable_spacy and spacy is not None:  # pragma: no branch
            try:
                self._nlp = spacy.blank("en")
                ruler = self._nlp.add_pipe("entity_ruler")
                ruler.add_patterns(
                    [
                        {"label": "ORG", "pattern": "Corporation"},
                        {"label": "ORG", "pattern": {"LOWER": "inc"}},
                        {"label": "ORG", "pattern": {"LOWER": "llc"}},
                    ]
                )
            except Exception:
                self._nlp = None

        self._industry_keywords = {
            "manufacturing": "Manufacturing",
            "technology": "Technology",
            "biotech": "Biotech",
            "pharma": "Pharmaceutical",
            "logistics": "Logistics",
            "warehouse": "Logistics",
            "energy": "Energy",
        }

    # Public API ---------------------------------------------------------
    def extract(self, text: str, summary: str = "") -> EntityExtractionResult:
        corpus = " ".join([summary, text]).strip()
        company, company_conf = self._extract_company(corpus)
        location, location_conf = self._extract_location(corpus)
        industry, industry_conf = self._classify_industry(corpus)
        return EntityExtractionResult(
            company=company,
            company_confidence=company_conf,
            location=location,
            location_confidence=location_conf,
            industry=industry,
            industry_confidence=industry_conf,
        )

    # Implementation details --------------------------------------------
    def _extract_company(self, corpus: str) -> tuple[Optional[str], float]:
        if not corpus:
            return None, 0.0

        if self._nlp is not None:  # pragma: no branch - optional dependency
            doc = self._nlp(corpus)
            orgs = [ent.text.strip(",. ") for ent in doc.ents if ent.label_.upper() == "ORG"]
            if orgs:
                return orgs[0], 0.9

        import re

        company_pattern = re.compile(
            r"\b([A-Z][A-Za-z0-9&'\-]+(?:\s+[A-Z][A-Za-z0-9&'\-]+){0,3})\b"
            r"(?:,?\s+(Inc|LLC|Ltd|Corporation|Corp|Company))?"
        )
        match = company_pattern.search(corpus)
        if match:
            base = match.group(1).strip(",. ")
            suffix = match.group(2)
            if suffix:
                company = f"{base} {suffix}".strip()
                confidence = 0.75
            else:
                company = base
                confidence = 0.6
            return company, confidence

        camel_case = re.search(r"\b([A-Z][A-Za-z]+(?:[A-Z][a-z]+)+)\b", corpus)
        if camel_case:
            return camel_case.group(1), 0.5

        tokens = re.findall(r"[A-Z][a-zA-Z]+", corpus)
        if len(tokens) >= 2:
            return f"{tokens[0]} {tokens[1]}", 0.4
        return None, 0.0

    def _extract_location(self, corpus: str) -> tuple[Dict[str, Optional[str]], float]:
        import re

        location = {"city": None, "state": None, "country": None, "raw": None}
        if not corpus:
            return location, 0.0

        match = re.search(r"([A-Z][A-Za-z\- ]+),\s*([A-Z]{2})\b", corpus)
        if match:
            city = match.group(1).strip()
            state = match.group(2).upper()
            location.update({"city": city, "state": state, "country": "USA", "raw": match.group(0)})
            return location, 0.8

        match = re.search(r"in\s+([A-Z][A-Za-z\- ]+),\s*([A-Z]{2})", corpus)
        if match:
            location.update(
                {
                    "city": match.group(1).strip(),
                    "state": match.group(2).upper(),
                    "country": "USA",
                    "raw": match.group(0),
                }
            )
            return location, 0.6

        match = re.search(r"([A-Z][A-Za-z\- ]+),\s*(United States|USA|US)", corpus)
        if match:
            location.update(
                {"city": match.group(1).strip(), "country": "USA", "raw": match.group(0)}
            )
            return location, 0.5

        match = re.search(r"in\s+([A-Z][A-Za-z\- ]+)(?:(?=\s|\.|,)|$)", corpus)
        if match:
            city = match.group(1).strip().rstrip(".,")
            location.update({"city": city, "country": None, "raw": match.group(0)})
            return location, 0.3

        return location, 0.0

    def _classify_industry(self, corpus: str) -> tuple[Optional[str], float]:
        lowered = corpus.lower()
        for keyword, label in self._industry_keywords.items():
            if keyword in lowered:
                return label, 0.6
        return None, 0.0


__all__ = ["EntityExtractor", "EntityExtractionResult"]
