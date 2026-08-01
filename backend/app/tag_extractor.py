"""
tag_extractor.py
------------------------------------------------------------------
Generates suggested tags from a product's title + features + price,
using a mix of:
  - spaCy PhraseMatcher for category detection (fixed taxonomy)
  - a pure price-comparison rule for budget-tier (fixed taxonomy)
  - regex for numeric spec tags (e.g. "16000-dpi", "120-hz")
  - spaCy noun-chunk extraction for freeform descriptive tags

Nothing here is saved to the DB — this only produces a list of
ExtractedTag suggestions for the admin to review/edit before saving,
per the preview -> confirm flow in routers/admin.py.
------------------------------------------------------------------
"""

import re
from dataclasses import dataclass
from typing import List, Optional

import spacy
from spacy.matcher import PhraseMatcher

from app.tag_config import (
    BUDGET_TIER_THRESHOLDS,
    CATEGORIES,
    DEFAULT_BUDGET_TIER_THRESHOLDS,
    FREEFORM_STOPWORDS,
    MAX_FREEFORM_TAGS,
    SPEC_PATTERNS,
)

# Load once at import time — loading the model per-request would be slow.
# Requires: python -m spacy download en_core_web_sm
_nlp = spacy.load("en_core_web_sm")

# Build the category PhraseMatcher once, at import time.
_category_matcher = PhraseMatcher(_nlp.vocab, attr="LOWER")
for _cat in CATEGORIES:
    _patterns = [_nlp.make_doc(phrase) for phrase in _cat["phrases"]]
    _category_matcher.add(_cat["name"], _patterns)


@dataclass
class ExtractedTag:
    name: str        # slugified tag value, e.g. "gaming-mouse", "16000-dpi"
    tag_type: str     # "category" / "budget_tier" / "spec" / "freeform"


def slugify(text: str) -> str:
    """Lowercase, replace whitespace with hyphens, strip non alnum/hyphen chars."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_category(doc) -> Optional[str]:
    """
    Return the single best-matching category name, or None.
    CATEGORIES is ordered most-specific-first, so we return the first
    entry (in that priority order) that had any match in the text.
    """
    matches = _category_matcher(doc)
    matched_names = {_nlp.vocab.strings[match_id] for match_id, _, _ in matches}
    for cat in CATEGORIES:
        if cat["name"] in matched_names:
            return cat["name"]
    return None


def extract_budget_tier(category: Optional[str], price_amount: Optional[float]) -> Optional[str]:
    """Pure rule-based budget/mid-range/premium classification by price."""
    if price_amount is None:
        return None

    thresholds = BUDGET_TIER_THRESHOLDS.get(category, DEFAULT_BUDGET_TIER_THRESHOLDS)

    if price_amount <= thresholds["budget_max"]:
        return "budget"
    elif price_amount <= thresholds["mid_max"]:
        return "mid-range"
    else:
        return "premium"


def extract_spec_tags(text: str) -> List[str]:
    """Regex-based numeric spec extraction, e.g. '16000 DPI' -> '16000-dpi'."""
    tags: List[str] = []
    for pattern, unit_label in SPEC_PATTERNS:
        for match in pattern.finditer(text):
            number = match.group(1)
            tag = f"{number}-{unit_label}"
            if tag not in tags:
                tags.append(tag)
    return tags


def extract_freeform_tags(doc, max_tags: int = MAX_FREEFORM_TAGS) -> List[str]:
    """
    Pull short descriptive noun phrases out of the text (e.g. "rgb lighting",
    "ergonomic grip") via spaCy noun-chunking, filtered against a stopword
    list and length limits to avoid junk tags.
    """
    candidates: List[str] = []

    for chunk in doc.noun_chunks:
        phrase = re.sub(r"[^a-z0-9\s-]", "", chunk.text.lower().strip())
        phrase = phrase.strip()
        if not phrase or len(phrase) < 3:
            continue

        words = phrase.split()
        if len(words) > 3:
            continue
        if any(word in FREEFORM_STOPWORDS for word in words):
            continue

        slug = slugify(phrase)
        if slug and slug not in candidates:
            candidates.append(slug)

        if len(candidates) >= max_tags:
            break

    return candidates


def extract_tags(
    title: Optional[str],
    features: Optional[List[str]],
    price_amount: Optional[float],
) -> List[ExtractedTag]:
    """
    Main entry point — run the full tagging pipeline against a product's
    fetched data and return a flat list of ExtractedTag suggestions.
    Called from the admin "preview" route, before anything is saved.
    """
    combined_text = title or ""
    if features:
        combined_text += " " + " ".join(features)

    doc = _nlp(combined_text)

    tags: List[ExtractedTag] = []
    seen_names = set()

    category = extract_category(doc)
    if category:
        tags.append(ExtractedTag(name=category, tag_type="category"))
        seen_names.add(category)

    budget_tier = extract_budget_tier(category, price_amount)
    if budget_tier:
        tags.append(ExtractedTag(name=budget_tier, tag_type="budget_tier"))
        seen_names.add(budget_tier)

    for spec_tag in extract_spec_tags(combined_text):
        if spec_tag not in seen_names:
            tags.append(ExtractedTag(name=spec_tag, tag_type="spec"))
            seen_names.add(spec_tag)

    for freeform_tag in extract_freeform_tags(doc):
        if freeform_tag not in seen_names:
            tags.append(ExtractedTag(name=freeform_tag, tag_type="freeform"))
            seen_names.add(freeform_tag)

    return tags