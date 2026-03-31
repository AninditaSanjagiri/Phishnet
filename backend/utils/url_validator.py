"""URL normalization and validation utilities."""
import re
from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Ensure URL has a scheme and is well-formed."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])
    except Exception:
        return False