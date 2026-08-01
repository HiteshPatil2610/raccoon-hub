"""
asin_utils.py
------------------------------------------------------------------
Extracts the 10-character ASIN from any Amazon.in product link,
regardless of whether it's a plain link or an affiliate-tagged one.
------------------------------------------------------------------
"""

import re
from typing import Optional

# Covers /dp/ASIN, /gp/product/ASIN, /gp/aw/d/ASIN, /exec/obidos/asin/ASIN, etc.
_ASIN_PATH_REGEX = re.compile(
    r"/(?:dp|gp/product|gp/aw/d|exec/obidos/asin|product-reviews)/"
    r"([A-Z0-9]{10})(?:[/?]|$)",
    re.IGNORECASE,
)

# Fallback: ASIN passed as a query parameter, e.g. ?ASIN=XXXXXXXXXX
_ASIN_QUERY_REGEX = re.compile(r"[?&]ASIN=([A-Z0-9]{10})", re.IGNORECASE)

# Last-resort: any standalone 10-char alphanumeric path/query token
_ASIN_TOKEN_REGEX = re.compile(r"^[A-Z0-9]{10}$", re.IGNORECASE)


def extract_asin(url: str) -> Optional[str]:
    """
    Extract a 10-character ASIN from a raw Amazon.in URL.
    Returns the ASIN in uppercase, or None if no ASIN could be found.
    Works on plain links, /dp/ links, /gp/product/ links, and
    affiliate-tagged links (the ?tag= param is ignored entirely).
    """
    if not url or not isinstance(url, str):
        return None

    match = _ASIN_PATH_REGEX.search(url)
    if match:
        return match.group(1).upper()

    match = _ASIN_QUERY_REGEX.search(url)
    if match:
        return match.group(1).upper()

    for segment in re.split(r"[/?&=]", url):
        segment = segment.strip()
        if _ASIN_TOKEN_REGEX.match(segment):
            return segment.upper()

    return None


def build_affiliate_url(asin: str, associate_tag: str) -> str:
    """
    Build a clean outbound affiliate link for the 'Buy on Amazon' button.
    This is constructed fresh from the ASIN + your tag — never reused
    from whatever link was originally pasted into the admin panel.
    """
    return f"https://www.amazon.in/dp/{asin}?tag={associate_tag}"