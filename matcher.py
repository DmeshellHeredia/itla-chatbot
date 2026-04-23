"""
Intent matching engine.

Pipeline:
  1. Keyword scoring   – exact token overlap (single + multi-word)
  2. Token-fuzzy hits  – soft hits for typos (fuzz.ratio >= 80)
  3. Variant-fuzzy     – RapidFuzz token_set_ratio against all variants
  4. Gated combination – evidence-weighted blend
  5. Threshold gate    – absolute floor before returning any result

Scoring rules
─────────────
• hits < 0.3 (no evidence):
    fz >= 80 → kw_fz = fz * 0.45   (near-identical variant, trust it)
    else     → kw_fz = fz * 0.12   (out-of-domain guard)
• hits ∈ [0.3, 1.5) and n_tokens >= 6 → kw * 0.65 + fz * 0.20
• else                                  → kw * 0.60 + fz * 0.40
• _MIN_SCORE = 20 (absolute floor)
"""

from __future__ import annotations

from rapidfuzz import fuzz, process

from config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, FUZZY_THRESHOLD
from knowledge_base import INTENTS
from preprocessor import normalize, normalize_list, tokenize

# ── Tuning constants ───────────────────────────────────────────────────────────
_TOKEN_FUZZY_THRESHOLD = 80   # Min fuzz.ratio(token, keyword) for a soft hit
_SOFT_HIT_WEIGHT       = 0.5  # How much each token-fuzzy match adds to hits
_HIGH_FZ_ESCAPE        = 80   # If hits≈0 but fz≥this, allow 45% contribution
_MIN_SCORE             = 20   # Absolute minimum to return any match

# ── Pre-computed per-intent data ───────────────────────────────────────────────
_NORM_VARIANTS: dict[str, list[str]] = {
    i["name"]: normalize_list(i["variants"]) for i in INTENTS
}

_SINGLE_KW:     dict[str, list[str]]      = {}
_SINGLE_KW_SET: dict[str, set[str]]       = {}
_MULTI_KW:      dict[str, list[list[str]]] = {}

for _intent in INTENTS:
    _name = _intent["name"]
    _single: list[str]       = []
    _multi:  list[list[str]] = []
    for _kw in normalize_list(_intent["keywords"]):
        _parts = _kw.split()
        if len(_parts) == 1:
            _single.append(_kw)
        else:
            _multi.append(_parts)
    _SINGLE_KW[_name]     = _single
    _SINGLE_KW_SET[_name] = set(_single)
    _MULTI_KW[_name]      = _multi


# ── 1 + 2. Keyword scoring with token-fuzzy typo tolerance ─────────────────────

def _keyword_score(tokens: list[str], intent: dict) -> tuple[float, float]:
    """
    Returns (score_0_to_100, hits_float).

    hits is a float because token-fuzzy soft hits contribute _SOFT_HIT_WEIGHT (0.5).
    """
    name = intent["name"]
    norm_required = normalize_list(intent.get("required_words", []))

    # Hard gate: ALL required words must be present
    token_set = set(tokens)
    for req in norm_required:
        if req not in token_set:
            return 0.0, 0.0

    single_kws    = _SINGLE_KW[name]
    single_kw_set = _SINGLE_KW_SET[name]
    multi_kws     = _MULTI_KW[name]

    if not single_kws and not multi_kws:
        return 0.0, 0.0

    hits: float = 0.0

    # Exact single-keyword matches
    for kw in single_kws:
        if kw in token_set:
            hits += 1.0

    # Multi-word: ALL component tokens must appear (token-set check, no substring)
    for parts in multi_kws:
        if all(p in token_set for p in parts):
            hits += 1.5

    # Token-level fuzzy: typo tolerance
    # For each input token not already exactly matched, check similarity to all
    # single keywords.  Threshold 80 catches 1-2 char typos (tlefono→telefono,
    # careras→carreras, yncribo→inscribo) while rejecting unrelated words.
    already_exact = token_set.intersection(single_kw_set)
    for tok in tokens:
        if tok in already_exact or len(tok) < 4:  # skip short tokens (el, de, …)
            continue
        for kw in single_kws:
            if fuzz.ratio(tok, kw) >= _TOKEN_FUZZY_THRESHOLD:
                hits += _SOFT_HIT_WEIGHT
                break  # at most one soft hit per input token per intent

    total_kws = len(single_kws) + len(multi_kws)
    raw_score = (hits / total_kws) * 100
    return min(raw_score, 100.0), hits


# ── 3. Variant-level fuzzy ─────────────────────────────────────────────────────

def _fuzzy_score(norm_input: str, intent: dict) -> float:
    """Best RapidFuzz token_set_ratio against all normalised variants."""
    candidates = _NORM_VARIANTS[intent["name"]]
    if not candidates:
        return 0.0
    result = process.extractOne(norm_input, candidates, scorer=fuzz.token_set_ratio)
    return result[1] if result else 0.0


# ── 4. Evidence-gated combination ─────────────────────────────────────────────

def _combine(kw: float, fz: float, sem: float, hits: float, n_tokens: int) -> float:
    if hits < 0.3:
        # No keyword or typo evidence → gate heavily to reject out-of-domain.
        # Escape hatch requires n_tokens >= 2: a single-word query that happens to
        # be a token inside a longer variant (e.g. "carreras" inside "precio de las
        # carreras") would get token_set_ratio=100 for the wrong intent.
        kw_fz = fz * 0.45 if (fz >= _HIGH_FZ_ESCAPE and n_tokens >= 2) else fz * 0.12
    elif hits < 1.5 and n_tokens >= 6:
        # Weak evidence in a long query → keyword dominates; fuzzy is modest
        kw_fz = kw * 0.65 + fz * 0.20
    else:
        kw_fz = kw * 0.60 + fz * 0.40

    if sem > 0:
        return kw_fz * 0.55 + sem * 0.45
    return kw_fz


# ── Public API ─────────────────────────────────────────────────────────────────

MatchResult = dict


def match(user_input: str, semantic_scores: dict[str, float] | None = None) -> MatchResult | None:
    """
    Find the best-matching intent for *user_input*.
    Returns a result dict or None when nothing clears _MIN_SCORE.
    """
    norm_input = normalize(user_input)
    tokens     = tokenize(user_input)
    n_tokens   = len(tokens)

    scores: dict[str, float] = {}

    for intent in INTENTS:
        name       = intent["name"]
        kw, hits   = _keyword_score(tokens, intent)
        fz         = _fuzzy_score(norm_input, intent)
        sem        = (semantic_scores or {}).get(name, 0.0)
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