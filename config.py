# ─── Confidence Thresholds ────────────────────────────────────────────────────
CONFIDENCE_HIGH   = 65   # Direct answer
CONFIDENCE_MEDIUM = 35   # Best-guess answer with caveat
CONFIDENCE_LOW    = 15   # Fallback

# ─── Matching Weights ─────────────────────────────────────────────────────────
FUZZY_THRESHOLD   = 78   # Min RapidFuzz ratio to count a variant hit
KEYWORD_WEIGHT    = 0.55
SEMANTIC_WEIGHT   = 0.45
SEMANTIC_TOP_K    = 3    # Top-k candidates from semantic index

# ─── Sentence Transformer ─────────────────────────────────────────────────────
EMBEDDING_MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDINGS_CACHE  = ".cache/embeddings.pkl"

# ─── UI ───────────────────────────────────────────────────────────────────────
BOT_NAME          = "ITLA Assistant"
BOT_AVATAR        = "🎓"
