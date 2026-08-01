"""
asin_utils.py
------------------------------------------------------------------
Extracts the 10-character ASIN from any Amazon.in product link,
regardless of whether it's a plain link, an affiliate-tagged one, or
a shortened link (amzn.in / amzn.to). Shortened links don't contain
the ASIN at all - Amazon resolves them server-side via an HTTP
redirect - so we follow that redirect first, exactly like a browser
does when you click the link. This is not scraping: it's a single
redirect lookup on a link the admin explicitly pasted in, not
crawling or extracting page content.
------------------------------------------------------------------
"""

import logging
import re
from typing import Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger("asin_utils")

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

# Known Amazon link-shortener domains that don't contain the ASIN directly.
_SHORTENER_DOMAINS = {"amzn.in", "amzn.to", "a.co"}

_REQUEST_HEADERS = {
    # A fuller browser-like header set - some servers 404/503 requests that
    # look scripted. This is a best-effort improvement, not a guarantee:
    # Amazon's bot detection can and does block plain scripted requests
    # outright regardless of headers.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _is_shortened_link(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return any(host == d or host.endswith("." + d) for d in _SHORTENER_DOMAINS)
    except ValueError:
        return False


def _resolve_short_link(url: str) -> Optional[str]:
    """
    Follow the redirect chain of a shortened Amazon link to get the real
    product URL. Uses GET directly - HEAD returns a flat 404 from
    Amazon's link shortener, it's not supported there. Returns None on
    any failure (including Amazon's bot-detection blocking the request
    outright, which does happen) so the caller can fail gracefully with
    a clear message rather than a crash.
    """
    try:
        resp = requests.get(
            url, allow_redirects=True, timeout=8, headers=_REQUEST_HEADERS, stream=True
        )
        resp.close()  # we only need resp.url, not the page body
        if resp.status_code >= 400:
            logger.warning("Short link resolution got HTTP %s for %s", resp.status_code, url)
            return None
        return resp.url
    except requests.RequestException as exc:
        logger.warning("Failed to resolve shortened link %s: %s", url, exc)
        return None


def _extract_asin_from_plain_url(url: str) -> Optional[str]:
    """The original extraction logic, for URLs that already contain the ASIN."""
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


def extract_asin(url: str) -> Optional[str]:
    """
    Extract a 10-character ASIN from a raw Amazon.in URL.
    Returns the ASIN in uppercase, or None if no ASIN could be found.
    Works on plain links, /dp/ links, /gp/product/ links,
    affiliate-tagged links (the ?tag= param is ignored entirely),
    and shortened links (amzn.in / amzn.to / a.co), which are resolved
    via redirect first since they don't contain the ASIN directly.
    """
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    if _is_shortened_link(url):
        resolved = _resolve_short_link(url)
        if not resolved:
            return None
        return _extract_asin_from_plain_url(resolved)

    return _extract_asin_from_plain_url(url)


def build_affiliate_url(asin: str, associate_tag: str) -> str:
    """
    Build a clean outbound affiliate link for the 'Buy on Amazon' button.
    This is constructed fresh from the ASIN + your tag — never reused
    from whatever link was originally pasted into the admin panel.
    """
    return f"https://www.amazon.in/dp/{asin}?tag={associate_tag}"