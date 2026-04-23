"""
Intent matching engine.

Pipeline (fast → slow):
  1. Keyword scoring  – weighted token overlap
  2. Fuzzy matching   – RapidFuzz against all variants
  3. Combined score   – max of both layers
"""

from __future__ import annotations

from rapidfuzz import fuzz, process

from config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, FUZZY_THRESHOLD
from knowledge_base import INTENTS
from preprocessor import normalize, normalize_list, tokenize


# ── Pre-computed normalized variants per intent ────────────────────────────────
_NORM_VARIANTS: dict[str, list[str]] = {
    intent["name"]: normalize_list(intent["variants"]) for intent in INTENTS
}

_NORM_KEYWORDS: dict[str, list[str]] = {
    intent["name"]: normalize_list(intent["keywords"]) for intent in INTENTS
}


# ── 1. Keyword scoring ─────────────────────────────────────────────────────────

def _keyword_score(tokens: list[str], intent: dict) -> float:
    """
    Score 0-100 based on token overlap with intent keywords.
    Required-words logic: if any required word is absent → 0.
    """
    norm_keywords = _NORM_KEYWORDS[intent["name"]]
    norm_required = normalize_list(intent.get("required_words", []))

    # Hard gate: all required words must be present
    for req in norm_required:
        if req not in tokens:
            return 0.0

    if not norm_keywords:
        return 0.0

    hits = sum(1 for kw in norm_keywords if kw in tokens)

    # Boost exact multi-word keyword matches
    norm_input = " ".join(tokens)
    exact_boost = sum(10 for kw in norm_keywords if " " in kw and kw in norm_input)

    raw = (hits / len(norm_keywords)) * 100 + exact_boost
    return min(raw, 100.0)


# ── 2. Fuzzy matching ──────────────────────────────────────────────────────────

def _fuzzy_score(norm_input: str, intent: dict) -> float:
    """Best RapidFuzz partial_ratio score against all normalized variants."""
    candidates = _NORM_VARIANTS[intent["name"]]
    if not candidates:
        return 0.0

    result = process.extractOne(
        norm_input,
        candidates,
        scorer=fuzz.token_set_ratio,
    )
    return result[1] if result else 0.0


# ── Public API ─────────────────────────────────────────────────────────────────

MatchResult = dict  # {"intent": dict, "score": float, "method": str}


def match(user_input: str, semantic_scores: dict[str, float] | None = None) -> MatchResult | None:
    """
    Find the best-matching intent for `user_input`.

    Parameters
    ----------
    user_input      : raw user message
    semantic_scores : optional dict {intent_name: float 0-100} from semantic layer

    Returns
    -------
    Best match dict or None if nothing clears CONFIDENCE_LOW.
    """
    norm_input = normalize(user_input)
    tokens = tokenize(user_input)

    scores: dict[str, float] = {}

    for intent in INTENTS:
        name = intent["name"]

        kw  = _keyword_score(tokens, intent)
        fz  = _fuzzy_score(norm_input, intent)
        sem = (semantic_scores or {}).get(name, 0.0)

        # Combine: take the dominant keyword/fuzzy signal, blend with semantic
        keyword_fuzzy = max(kw, fz)

        if sem > 0:
            combined = keyword_fuzzy * 0.55 + sem * 0.45
        else:
            combined = keyword_fuzzy

        scores[name] = round(combined, 2)

    best_name = max(scores, key=scores.get)
    best_score = scores[best_name]

    if best_score < 10:
        return None

    best_intent = next(i for i in INTENTS if i["name"] == best_name)
    return {"intent": best_intent, "score": best_score, "scores": scores}


def confidence_label(score: float) -> str:
    if score >= CONFIDENCE_HIGH:
        return "high"
    if score >= CONFIDENCE_MEDIUM:
        return "medium"
    return "low"
