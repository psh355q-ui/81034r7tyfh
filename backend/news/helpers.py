# -*- coding: utf-8 -*-
"""
Utility helpers for the RSS news crawler.
All functions are UTF‑8 safe and contain no null bytes.
"""
import hashlib
import html
import re
from typing import List, Set

# ---------------------------------------------------------------------------
# HTML cleaning
# ---------------------------------------------------------------------------
def clean_html(raw_html: str) -> str:
    """Return a plain‑text version of *raw_html*.
    - Unescape HTML entities.
    - Remove HTML tags.
    - Collapse whitespace.
    """
    # Unescape entities like &amp; &quot; etc.
    text = html.unescape(raw_html)
    # Strip tags using a simple regex (good enough for RSS snippets).
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse multiple whitespace characters into a single space.
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ---------------------------------------------------------------------------
# Duplicate detection (SHA‑256 of title + content)
# ---------------------------------------------------------------------------
def hash_content(title: str, content: str) -> str:
    """Create a deterministic SHA‑256 hash for a news article.
    The hash is used as a unique identifier to avoid duplicate storage.
    """
    # Ensure we always work with UTF‑8 bytes.
    combined = f"{title}\n{content}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()

# ---------------------------------------------------------------------------
# Keyword relevance
# ---------------------------------------------------------------------------
# Example keyword set – can be extended later via configuration.
DEFAULT_KEYWORDS: Set[str] = {
    "ai",
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "semiconductor",
    "chip",
    "gpu",
    "nvidia",
    "amd",
    "tesla",
    "google",
    "microsoft",
    "amazon",
    "meta",
    "facebook",
    "intel",
    "qualcomm",
    "tsmc",
    "micron",
    "circuit",
    "processor",
    "data center",
    "cloud",
    "software",
    "hardware",
    "stock",
    "market",
    "earnings",
    "revenue",
    "profit",
    "loss",
    "growth",
    "forecast",
    "price",
    "valuation",
    "investment",
    "trading",
    "risk",
    "regulation",
    "policy",
    "government",
    "regulatory",
    "technology",
    "innovation",
}

def is_relevant(text: str, keywords: Set[str] = DEFAULT_KEYWORDS) -> bool:
    """Return ``True`` if *text* contains any of the supplied *keywords*.
    The check is case‑insensitive and works on plain text.
    """
    lowered = text.lower()
    for kw in keywords:
        if kw.lower() in lowered:
            return True
    return False
