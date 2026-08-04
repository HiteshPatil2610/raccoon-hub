"""
ai_client.py
------------------------------------------------------------------
Thin wrapper around the Gemini API (free tier - see config.py).
Currently used for AI-written product blurbs; the embed_text()
function is here ready for the semantic search / recommendations /
duplicate-detection features to build on next, so they all share one
client setup instead of duplicating it.

Every function here fails soft (returns None) rather than raising -
a missing API key, rate limit, or network hiccup should never break
product preview/save, it should just mean no AI blurb this time.
------------------------------------------------------------------
"""

import logging
from typing import List, Optional

from google import genai
from google.genai import types

from app.config import settings

logger = logging.getLogger("ai_client")

_TEXT_MODEL = "gemini-flash-latest"
_EMBEDDING_MODEL = "gemini-embedding-001"

_client: Optional[genai.Client] = None


def _get_client() -> Optional[genai.Client]:
    global _client
    if not settings.GEMINI_API_KEY:
        return None
    if _client is None:
        _client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(client_args={"trust_env": False}),
        )
    return _client


def generate_product_blurb(title: Optional[str], features: List[str]) -> Optional[str]:
    """
    Generate a short, compelling 2-3 sentence product description from
    the raw title + features list. Returns None if the API key isn't
    configured yet, or if the call fails for any reason.
    """
    client = _get_client()
    if client is None:
        return None

    if not title:
        return None

    features_text = "\n".join(f"- {f}" for f in features) if features else "(no listed features)"

    prompt = (
        "Write a short, compelling product description for an online store, "
        "based on the raw Amazon listing data below. 2-3 sentences, no marketing "
        "fluff or made-up claims - only describe what's actually stated. Don't "
        "repeat the title verbatim. No markdown, no quotation marks, plain text only.\n\n"
        f"Title: {title}\n"
        f"Features:\n{features_text}"
    )

    try:
        response = client.models.generate_content(model=_TEXT_MODEL, contents=prompt)
        text = (response.text or "").strip()
        return text or None
    except Exception as exc:  # noqa: BLE001 - any API/network failure should fail soft
        logger.warning("Gemini blurb generation failed: %s", exc)
        return None


def embed_text(text: str) -> Optional[List[float]]:
    """
    Get an embedding vector for a piece of text. Foundation for semantic
    search / recommendations / duplicate detection - not wired into any
    route yet. Returns None on missing key or any failure.
    """
    client = _get_client()
    if client is None or not text:
        return None

    try:
        response = client.models.embed_content(model=_EMBEDDING_MODEL, contents=text)
        if response.embeddings:
            return response.embeddings[0].values
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini embedding failed: %s", exc)
        return None