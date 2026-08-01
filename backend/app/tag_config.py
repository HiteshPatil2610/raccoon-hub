"""
tag_config.py
------------------------------------------------------------------
Configuration data used by tag_extractor.py. Edit this file to add
new product categories, adjust budget-tier price thresholds, add new
spec patterns to detect, or expand the freeform-tag stopword list.

Nothing in here talks to spaCy or the DB directly — it's pure config.
------------------------------------------------------------------
"""

import re

# ------------------------------------------------------------------
# CATEGORIES — ordered most-specific first. The first matching name
# in this list wins if multiple categories match the same text (e.g.
# "gaming mouse" should tag as "gaming-mouse", not just "mouse").
# ------------------------------------------------------------------
CATEGORIES = [
    {"name": "gaming-mouse", "phrases": ["gaming mouse", "gaming mice"]},
    {"name": "mouse", "phrases": ["mouse", "wireless mouse", "mice"]},
    {"name": "mechanical-keyboard", "phrases": ["mechanical keyboard"]},
    {"name": "keyboard", "phrases": ["keyboard"]},
    {"name": "headphone", "phrases": ["headphone", "headphones", "headset", "earphone", "earbuds"]},
    {"name": "monitor", "phrases": ["monitor", "display"]},
    {"name": "webcam", "phrases": ["webcam"]},
    {"name": "microphone", "phrases": ["microphone", "mic"]},
    {"name": "laptop", "phrases": ["laptop", "notebook"]},
    {"name": "smartphone", "phrases": ["smartphone", "mobile phone"]},
    {"name": "power-bank", "phrases": ["power bank", "powerbank"]},
    {"name": "smartwatch", "phrases": ["smartwatch", "smart watch"]},
    {"name": "speaker", "phrases": ["speaker", "bluetooth speaker"]},
]

# ------------------------------------------------------------------
# BUDGET TIER THRESHOLDS — per category, in INR.
# price <= budget_max        -> "budget"
# budget_max < price <= mid_max -> "mid-range"
# price > mid_max            -> "premium"
# Add an entry per category as your catalog grows; anything not
# listed falls back to DEFAULT_BUDGET_TIER_THRESHOLDS.
# ------------------------------------------------------------------
BUDGET_TIER_THRESHOLDS = {
    "gaming-mouse": {"budget_max": 1200, "mid_max": 3000},
    "mouse": {"budget_max": 800, "mid_max": 2000},
    "mechanical-keyboard": {"budget_max": 2500, "mid_max": 6000},
    "keyboard": {"budget_max": 1000, "mid_max": 2500},
    "headphone": {"budget_max": 1500, "mid_max": 5000},
    "monitor": {"budget_max": 10000, "mid_max": 20000},
    "laptop": {"budget_max": 40000, "mid_max": 70000},
    "smartphone": {"budget_max": 15000, "mid_max": 30000},
    "smartwatch": {"budget_max": 3000, "mid_max": 8000},
    "speaker": {"budget_max": 1500, "mid_max": 4000},
    "power-bank": {"budget_max": 1000, "mid_max": 2000},
    "webcam": {"budget_max": 1500, "mid_max": 4000},
    "microphone": {"budget_max": 1500, "mid_max": 4000},
}

DEFAULT_BUDGET_TIER_THRESHOLDS = {"budget_max": 1500, "mid_max": 5000}

# ------------------------------------------------------------------
# SPEC PATTERNS — regex + normalized unit label. Matched against the
# combined title + features text. Add more (e.g. "mp" for camera
# megapixels, "inch" for screen size) as needed.
# Each tuple: (compiled_pattern, unit_label)
# The pattern must have exactly one capture group: the number.
# ------------------------------------------------------------------
SPEC_PATTERNS = [
    (re.compile(r"(\d{3,6})\s?dpi\b", re.IGNORECASE), "dpi"),
    (re.compile(r"(\d{2,4})\s?hz\b", re.IGNORECASE), "hz"),
    (re.compile(r"(\d{3,6})\s?mah\b", re.IGNORECASE), "mah"),
    (re.compile(r"(\d{1,4})\s?gb\b", re.IGNORECASE), "gb"),
    (re.compile(r"(\d{1,2}(?:\.\d)?)\s?ghz\b", re.IGNORECASE), "ghz"),
    (re.compile(r"(\d{1,3})\s?w\b", re.IGNORECASE), "watt"),
    (re.compile(r"(\d{1,2}(?:\.\d)?)\s?(?:inch|\")\b", re.IGNORECASE), "inch"),
]

# ------------------------------------------------------------------
# FREEFORM STOPWORDS — junk words filtered out of noun-chunk based
# freeform tag suggestions so you don't get tags like "the-product".
# ------------------------------------------------------------------
FREEFORM_STOPWORDS = {
    "product", "item", "amazon", "quality", "pack", "piece", "set",
    "pieces", "type", "model", "brand", "design", "style", "feature",
    "features", "use", "user", "users", "price", "value", "money",
    "day", "days", "time", "way", "thing", "things", "it", "this",
    "that", "these", "those", "one", "some", "any", "all", "new",
}

# Maximum number of freeform tags suggested per product
MAX_FREEFORM_TAGS = 8