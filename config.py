# ─── Umbrales de confianza ────────────────────────────────────────────────────
# Definen en qué rango de puntuación cae cada nivel de certeza del bot.
# Una puntuación >= CONFIDENCE_HIGH produce una respuesta directa y corta.
# Entre CONFIDENCE_MEDIUM y CONFIDENCE_HIGH se usa la respuesta extendida.
# Por debajo de CONFIDENCE_MEDIUM se añade un aviso de baja confianza.
#
# Guía de ajuste:
#   - Subir CONFIDENCE_HIGH  → menos respuestas directas, más respuestas extendidas
#   - Bajar CONFIDENCE_HIGH  → el bot responde con más confianza (riesgo de falsos positivos)
#   - Subir CONFIDENCE_MEDIUM → más respuestas con aviso de baja confianza
#   - Bajar CONFIDENCE_MEDIUM → el bot acepta coincidencias más débiles sin advertir al usuario
CONFIDENCE_HIGH   = 65   # Respuesta directa y confiable
CONFIDENCE_MEDIUM = 35   # Respuesta aproximada con advertencia
CONFIDENCE_LOW    = 15   # Respaldo (actualmente no usado como umbral propio)

# ─── Pesos de coincidencia ────────────────────────────────────────────────────
# FUZZY_THRESHOLD: puntuación mínima de RapidFuzz para considerar una variante
#   como coincidencia válida. 78 tolera errores de 1-2 caracteres (p.ej. "careras"
#   → "carreras") sin aceptar palabras sin relación.
#   Rango recomendado: 70–85. Bajar aumenta la tolerancia a errores pero
#   también la cantidad de falsos positivos.
#
# KEYWORD_WEIGHT / SEMANTIC_WEIGHT: proporción de cada señal en la puntuación
#   final. Deben sumar ≈ 1.0 para mantener la escala 0–100.
#   Aumentar SEMANTIC_WEIGHT mejora la comprensión de paráfrasis pero requiere
#   que el motor semántico (FAISS) esté disponible.
#
# SEMANTIC_TOP_K: cuántos candidatos semánticos se recuperan del índice FAISS
#   antes de fusionarlos con las puntuaciones de palabras clave.
#   Valores más altos aumentan el recall semántico pero ralentizan la búsqueda.
FUZZY_THRESHOLD   = 78   # Ratio mínimo de RapidFuzz para una coincidencia válida
KEYWORD_WEIGHT    = 0.55  # Peso del motor de palabras clave en la puntuación combinada
SEMANTIC_WEIGHT   = 0.45  # Peso del motor semántico en la puntuación combinada
SEMANTIC_TOP_K    = 3     # Número de candidatos semánticos a recuperar del índice

# ─── Modelo de embeddings ─────────────────────────────────────────────────────
# Modelo multilingüe compacto de sentence-transformers (~117 MB). Soporta
# español e inglés y corre eficientemente en CPU sin necesidad de GPU.
#
# Para cambiar el modelo:
#   1. Reemplazar EMBEDDING_MODEL por otro ID de sentence-transformers.
#   2. Borrar el archivo EMBEDDINGS_CACHE para forzar el recálculo de vectores.
#      (Si no se borra, se usarán vectores del modelo anterior con el nuevo,
#       lo que produce resultados incorrectos.)
#
# EMBEDDINGS_CACHE: ruta donde se guardan los vectores precalculados para evitar
#   recalcularlos en cada arranque (se genera la primera vez que se ejecuta).
EMBEDDING_MODEL   = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDINGS_CACHE  = ".cache/embeddings.pkl"

# ─── Interfaz de usuario ──────────────────────────────────────────────────────
# Nombre y avatar que se muestran en la interfaz gráfica del chatbot.
BOT_NAME          = "ITLA Assistant"
BOT_AVATAR        = "🎓"
