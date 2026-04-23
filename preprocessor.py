"""Text preprocessing utilities."""

import re
import unicodedata


def remove_accents(text: str) -> str:
    """'café' → 'cafe'"""
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize(text: str) -> str:
    """Full normalization pipeline: lowercase → no accents → no punctuation → clean whitespace."""
    text = text.lower()
    text = remove_accents(text)
    text = re.sub(r"[^\w\s]", " ", text)   # strip punctuation
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    """Return list of normalized tokens."""
    return normalize(text).split()


def normalize_list(phrases: list[str]) -> list[str]:
    return [normalize(p) for p in phrases]
