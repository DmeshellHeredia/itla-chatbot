"""
Motor de coincidencia de intenciones (Intent Matching Engine).

Pipeline de procesamiento:
  1. Puntuación por palabras clave  – solapamiento exacto de tokens (simples y multi-palabra)
  2. Hits difusos por token          – coincidencias suaves para errores tipográficos (fuzz.ratio >= 80)
  3. Variantes difusas               – token_set_ratio de RapidFuzz contra todas las variantes del intent
  4. Combinación ponderada           – mezcla ponderada según evidencia acumulada
  5. Umbral mínimo                   – piso absoluto antes de devolver cualquier resultado

Reglas de puntuación
─────────────────────
• hits < 0.3 (sin evidencia de palabras clave):
    fz >= 80 → kw_fz = fz * 0.45   (variante casi idéntica, se confía en ella)
    si no    → kw_fz = fz * 0.12   (guardia para consultas fuera del dominio)
• hits ∈ [0.3, 1.5) y n_tokens >= 6 → kw * 0.65 + fz * 0.20
• en cualquier otro caso             → kw * 0.60 + fz * 0.40
• _MIN_SCORE = 20 (puntaje mínimo absoluto para retornar una coincidencia)
"""

from __future__ import annotations

from rapidfuzz import fuzz, process

from config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, FUZZY_THRESHOLD
from knowledge_base import INTENTS
from preprocessor import normalize, normalize_list, tokenize

# ── Constantes de ajuste ───────────────────────────────────────────────────────
# Umbral mínimo de similitud (fuzz.ratio) para considerar un token como "soft hit"
_TOKEN_FUZZY_THRESHOLD = 80

# Peso que suma cada coincidencia difusa de token al contador de hits
# (menor que 1.0 para diferenciarla de una coincidencia exacta)
_SOFT_HIT_WEIGHT = 0.5

# Si los hits son ~0 pero la similitud difusa supera este valor,
# se permite una contribución del 45% en lugar del 12% habitual
_HIGH_FZ_ESCAPE = 80

# Puntaje mínimo absoluto para considerar que hay una coincidencia válida;
# si el mejor intent no lo alcanza, se devuelve None
_MIN_SCORE = 20

# ── Datos pre-computados por intent ───────────────────────────────────────────
# Se normalizan las variantes de cada intent una sola vez al cargar el módulo
# para evitar recalcularlas en cada llamada a match()
_NORM_VARIANTS: dict[str, list[str]] = {
    i["name"]: normalize_list(i["variants"]) for i in INTENTS
}

# Palabras clave de token único (una sola palabra) por intent
_SINGLE_KW:     dict[str, list[str]]      = {}

# Mismo conjunto como set para búsquedas O(1) de exactitud
_SINGLE_KW_SET: dict[str, set[str]]       = {}

# Palabras clave multi-palabra (listas de tokens) por intent
_MULTI_KW:      dict[str, list[list[str]]] = {}

# Se separan las keywords en simples vs multi-palabra al iniciar el módulo
for _intent in INTENTS:
    _name = _intent["name"]
    _single: list[str]       = []
    _multi:  list[list[str]] = []
    for _kw in normalize_list(_intent["keywords"]):
        _parts = _kw.split()
        if len(_parts) == 1:
            _single.append(_kw)
        else:
            # Cada keyword multi-palabra se guarda como lista de sus tokens
            _multi.append(_parts)
    _SINGLE_KW[_name]     = _single
    _SINGLE_KW_SET[_name] = set(_single)
    _MULTI_KW[_name]      = _multi


# ── 1 + 2. Puntuación por palabras clave con tolerancia a errores tipográficos ─

def _keyword_score(tokens: list[str], intent: dict) -> tuple[float, float]:
    """
    Calcula el puntaje de coincidencia de palabras clave para un intent dado.

    Combina coincidencias exactas (hits = 1.0 por keyword simple, 1.5 por
    keyword multi-palabra) con coincidencias difusas de token (hits += 0.5)
    para tolerar errores tipográficos frecuentes.

    Retorna:
        (score_0_a_100, hits_float)
        - score: porcentaje de keywords cubiertas, acotado a 100
        - hits: conteo flotante de coincidencias (incluye soft hits por typos)
    """
    name = intent["name"]

    # Verificar que todas las palabras obligatorias estén presentes en la entrada
    norm_required = normalize_list(intent.get("required_words", []))
    token_set = set(tokens)
    for req in norm_required:
        if req not in token_set:
            # Si falta alguna palabra requerida, el puntaje es cero inmediatamente
            return 0.0, 0.0

    single_kws    = _SINGLE_KW[name]
    single_kw_set = _SINGLE_KW_SET[name]
    multi_kws     = _MULTI_KW[name]

    # Si el intent no tiene keywords definidas, no se puede puntuar
    if not single_kws and not multi_kws:
        return 0.0, 0.0

    hits: float = 0.0

    # Paso 1: coincidencias exactas de keywords de un solo token
    for kw in single_kws:
        if kw in token_set:
            hits += 1.0

    # Paso 2: keywords multi-palabra — todos sus tokens deben aparecer en la entrada
    # (comprobación por conjunto de tokens, no por subcadena de texto)
    for parts in multi_kws:
        if all(p in token_set for p in parts):
            hits += 1.5  # pesa más porque es una coincidencia más específica

    # Paso 3: tolerancia a errores tipográficos a nivel de token
    # Para cada token de entrada que NO sea ya una coincidencia exacta,
    # se compara con todas las keywords simples del intent.
    # Umbral 80 captura errores de 1-2 caracteres (p.ej. "tlefono" → "telefono",
    # "careras" → "carreras") sin aceptar palabras sin relación.
    already_exact = token_set.intersection(single_kw_set)
    for tok in tokens:
        # Se omiten tokens ya exactos y tokens muy cortos (artículos, preposiciones…)
        if tok in already_exact or len(tok) < 4:
            continue
        for kw in single_kws:
            if fuzz.ratio(tok, kw) >= _TOKEN_FUZZY_THRESHOLD:
                hits += _SOFT_HIT_WEIGHT
                break  # máximo un soft hit por token de entrada por intent

    total_kws = len(single_kws) + len(multi_kws)
    raw_score = (hits / total_kws) * 100
    return min(raw_score, 100.0), hits


# ── 3. Puntuación difusa a nivel de variante ──────────────────────────────────

def _fuzzy_score(norm_input: str, intent: dict) -> float:
    """
    Compara la entrada normalizada contra todas las variantes pre-computadas
    del intent usando RapidFuzz token_set_ratio.

    token_set_ratio es robusto ante palabras extra o reordenadas, lo que lo
    hace ideal para capturar paráfrasis del usuario que no coinciden
    palabra por palabra con ninguna variante.

    Retorna el mejor puntaje encontrado (0–100), o 0.0 si no hay variantes.
    """
    candidates = _NORM_VARIANTS[intent["name"]]
    if not candidates:
        return 0.0
    # process.extractOne encuentra la variante más similar en una sola pasada
    result = process.extractOne(norm_input, candidates, scorer=fuzz.token_set_ratio)
    return result[1] if result else 0.0


# ── 4. Combinación ponderada por evidencia ────────────────────────────────────

def _combine(kw: float, fz: float, sem: float, hits: float, n_tokens: int) -> float:
    """
    Combina los puntajes de palabras clave (kw), difuso (fz) y semántico (sem)
    en un único puntaje final, ajustando los pesos según la cantidad de evidencia
    acumulada (hits) y la longitud de la consulta (n_tokens).

    La lógica de pesos es:
    - Sin evidencia (hits < 0.3): se penaliza fuertemente para evitar falsos positivos
      en consultas fuera del dominio. Solo se permite alta contribución difusa si
      fz >= _HIGH_FZ_ESCAPE y la consulta tiene al menos 2 tokens (previene que
      una sola palabra corta active el escape hatch por coincidencia).
    - Evidencia débil en consulta larga (hits < 1.5 y n_tokens >= 6): la keyword
      domina más y se reduce el peso difuso, porque en oraciones largas la similitud
      difusa puede inflar el puntaje sin verdadera relevancia.
    - Evidencia normal: combinación estándar 60/40 keyword/difuso.

    Si hay puntaje semántico disponible (sem > 0), se mezcla con peso 45%
    para aprovechar la comprensión semántica profunda cuando esté disponible.
    """
    if hits < 0.3:
        # Sin evidencia de keywords: depender del difuso es arriesgado.
        # Escape hatch: si la similitud difusa es muy alta (≥80) Y la consulta
        # tiene al menos 2 tokens, se permite 45% de contribución difusa.
        # Con solo 1 token, el escape no aplica: evita que una sola palabra
        # corta active un intent por coincidencia fortuita de cadena.
        kw_fz = fz * 0.45 if (fz >= _HIGH_FZ_ESCAPE and n_tokens >= 2) else fz * 0.12
    elif hits < 1.5 and n_tokens >= 6:
        # Evidencia débil en consulta larga: keyword domina (65%) para mayor precisión.
        # En oraciones largas, el fuzzy puede inflar el puntaje sin relación real
        # (muchas palabras comunes generan similitud superficial), por eso se reduce.
        kw_fz = kw * 0.65 + fz * 0.20
    else:
        # Caso general: mezcla 60/40 keyword/difuso para equilibrio precisión-cobertura.
        kw_fz = kw * 0.60 + fz * 0.40

    # Incorporar puntaje semántico si está disponible.
    # 55/45 keyword-difuso/semántico: la semántica mejora paráfrasis pero
    # el motor de keywords sigue siendo el ancla principal del resultado.
    if sem > 0:
        return kw_fz * 0.55 + sem * 0.45
    return kw_fz


# ── API pública ────────────────────────────────────────────────────────────────

# Estructura del diccionario que retorna match():
#   {
#     "intent": dict,              ← dict completo del intent ganador (de knowledge_base)
#     "score":  float,             ← puntaje combinado 0–100 redondeado a 2 decimales
#     "scores": dict[str, float]  ← puntaje de TODOS los intents evaluados en esa consulta
#   }
# Ejemplo:
#   match("cómo me inscribo") →
#     {"intent": {...}, "score": 88.5, "scores": {"inscripcion": 88.5, "saludo": 12.0, ...}}
MatchResult = dict


def match(user_input: str, semantic_scores: dict[str, float] | None = None) -> MatchResult | None:
    """
    Encuentra el intent que mejor coincide con la entrada del usuario.

    Ejecuta el pipeline completo (keyword scoring → fuzzy → combinación ponderada)
    para cada intent registrado en la knowledge base, y retorna el mejor resultado
    siempre que supere el piso mínimo _MIN_SCORE.

    Args:
        user_input:       Texto original del usuario (sin preprocesar).
        semantic_scores:  Diccionario opcional {nombre_intent: puntaje_0_a_100}
                          proveniente de un modelo semántico externo (ej. embeddings).
                          Si es None o vacío, se omite la componente semántica.

    Retorna:
        Diccionario con las claves:
            - "intent": el dict completo del intent ganador (de knowledge_base)
            - "score":  puntaje combinado redondeado a 2 decimales (0–100)
            - "scores": dict con el puntaje de todos los intents evaluados
        O None si ningún intent alcanza _MIN_SCORE.
    """
    # Normalizar la entrada y tokenizarla para el análisis de keywords
    norm_input = normalize(user_input)
    tokens     = tokenize(user_input)
    n_tokens   = len(tokens)

    scores: dict[str, float] = {}

    # Evaluar cada intent con el pipeline completo (keyword → fuzzy → combinación)
    for intent in INTENTS:
        name       = intent["name"]
        # Puntuación por palabras clave (incluye coincidencias suaves para typos)
        kw, hits   = _keyword_score(tokens, intent)
        # Puntuación difusa a nivel de variante completa (token_set_ratio)
        fz         = _fuzzy_score(norm_input, intent)
        # Puntuación semántica externa (0.0 si el motor no está disponible)
        sem        = (semantic_scores or {}).get(name, 0.0)
        scores[name] = round(_combine(kw, fz, sem, hits, n_tokens), 2)

    # Seleccionar el intent con mayor puntaje combinado
    best_name  = max(scores, key=scores.get)
    best_score = scores[best_name]

    # Rechazar si no supera el umbral mínimo absoluto; evita respuestas irrelevantes
    # para consultas completamente fuera del dominio del bot
    if best_score < _MIN_SCORE:
        return None

    # Recuperar el dict completo del intent ganador desde la knowledge base
    best_intent = next(i for i in INTENTS if i["name"] == best_name)
    return {"intent": best_intent, "score": best_score, "scores": scores}


def confidence_label(score: float) -> str:
    """
    Convierte un puntaje numérico en una etiqueta de confianza legible.

    Los umbrales CONFIDENCE_HIGH y CONFIDENCE_MEDIUM se definen en config.py
    para facilitar el ajuste sin tocar este módulo.

    Retorna:
        "high"   si score >= CONFIDENCE_HIGH
        "medium" si score >= CONFIDENCE_MEDIUM
        "low"    en cualquier otro caso
    """
    if score >= CONFIDENCE_HIGH:
        return "high"
    if score >= CONFIDENCE_MEDIUM:
        return "medium"
    return "low"
