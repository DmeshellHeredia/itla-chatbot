"""
Intent matching engine.

Pipeline (fast → slow):
  1. Keyword scoring  – weighted token overlap (single + multi-word, token-based only)
  2. Fuzzy matching   – RapidFuzz against all variants
  3. Combined score   – gated by keyword evidence, not max()
  4. Minimum threshold – absolute floor before returning any match

Scoring rules
─────────────
• hits == 0  → fuzzy is unreliable; cap contribution at 15% (out-of-domain guard)
• hits == 1 and long query (6+ tokens) → weak evidence; reduced fuzzy weight
• hits >= 2  → full weighted blend (kw 60% + fz 40%)
• Minimum combined score of 22 before a result is returned
"""

from __future__ import annotations

from rapidfuzz import fuzz, process

from config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, FUZZY_THRESHOLD
from knowledge_base import INTENTS
from preprocessor import normalize, normalize_list, tokenize


# ── Pre-computed normalised data ───────────────────────────────────────────────
_NORM_VARIANTS: dict[str, list[str]] = {
    intent["name"]: normalize_list(intent["variants"]) for intent in INTENTS
}

# Keywords split into single-word and multi-word buckets at load time
_SINGLE_KW: dict[str, list[str]] = {}
_MULTI_KW:  dict[str, list[list[str]]] = {}

for _intent in INTENTS:
    _name = _intent["name"]
    _single, _multi = [], []
    for kw in normalize_list(_intent["keywords"]):
        parts = kw.split()
        if len(parts) == 1:
            _single.append(kw)
        else:
            _multi.append(parts)
    _SINGLE_KW[_name] = _single
    _MULTI_KW[_name]  = _multi


# ── 1. Keyword scoring ─────────────────────────────────────────────────────────

def _keyword_score(tokens: list[str], intent: dict) -> tuple[float, int]:
    """
    Returns (score_0_to_100, raw_hit_count).

    Multi-word keywords are matched by checking ALL component tokens are present
    in the token list — NOT by substring on the joined string (avoids false
    positives like 'cuanto cuesta' inside 'cuanto cuesta un iphone').
    """
    name = intent["name"]
    norm_required = normalize_list(intent.get("required_words", []))

    # Hard gate: every required word must be present
    for req in norm_required:
        if req not in tokens:
            return 0.0, 0

    single_kws = _SINGLE_KW[name]
    multi_kws  = _MULTI_KW[name]

    if not single_kws and not multi_kws:
        return 0.0, 0

    hits: float = 0.0

    for kw in single_kws:
        if kw in tokens:
            hits += 1.0

    # Multi-word: ALL component tokens must appear (token-set check, no substring)
    for parts in multi_kws:
        if all(p in tokens for p in parts):
            hits += 1.5   # slight weight for more specific phrase match

    total_kws = len(single_kws) + len(multi_kws)
    raw_score = (hits / total_kws) * 100
    return min(raw_score, 100.0), int(hits)


# ── 2. Fuzzy matching ──────────────────────────────────────────────────────────

def _fuzzy_score(norm_input: str, intent: dict) -> float:
    """Best RapidFuzz token_set_ratio score against all normalised variants."""
    candidates = _NORM_VARIANTS[intent["name"]]
    if not candidates:
        return 0.0

    result = process.extractOne(
        norm_input,
        candidates,
        scorer=fuzz.token_set_ratio,
    )
    return result[1] if result else 0.0


# ── 3. Gated combination ───────────────────────────────────────────────────────

def _combine(kw: float, fz: float, sem: float, hits: int, n_tokens: int) -> float:
    """
    Merge keyword, fuzzy, and semantic signals with evidence-gating.

    hits == 0     → fuzzy carries almost no weight (out-of-domain guard)
    hits == 1 and long query → reduced fuzzy weight
    hits >= 2     → full blend
    """
    if hits == 0:
        kw_fz = fz * 0.15           # near-zero; fuzzy alone cannot confirm a match
    elif hits == 1 and n_tokens >= 6:
        kw_fz = kw * 0.65 + fz * 0.20   # keyword dominates; fuzzy is cautious
    else:
        kw_fz = kw * 0.60 + fz * 0.40

    if sem > 0:
        return kw_fz * 0.55 + sem * 0.45
    return kw_fz


# ── Public API ─────────────────────────────────────────────────────────────────

#: Minimum combined score to return *any* match (below → fallback / None)
_MIN_SCORE = 22

MatchResult = dict


def match(user_input: str, semantic_scores: dict[str, float] | None = None) -> MatchResult | None:
    """
    Find the best-matching intent for *user_input*.

    Returns a result dict or None when no intent clears the minimum threshold.
    """
    norm_input = normalize(user_input)
    tokens     = tokenize(user_input)
    n_tokens   = len(tokens)

    scores: dict[str, float] = {}

    for intent in INTENTS:
        name = intent["name"]

        kw, hits = _keyword_score(tokens, intent)
        fz       = _fuzzy_score(norm_input, intent)
        sem      = (semantic_scores or {}).get(name, 0.0)

        scores[name] = round(_combine(kw, fz, sem, hits, n_tokens), 2)

    best_name  = max(scores, key=scores.get)
    best_score = scores[best_name]

    if best_score < _MIN_SCORE:
        return None

    best_intent = next(i for i in INTENTS if i["name"] == best_name)
    return {"intent": best_intent, "score": best_score, "scores": scores}


def confidence_label(score: float) -> str:
    if score >= CONFIDENCE_HIGH:
        return "high"
    if score >= CONFIDENCE_MEDIUM:
        return "medium"
    return "low"