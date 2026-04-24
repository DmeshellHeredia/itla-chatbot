"""
Capa de búsqueda semántica del chatbot ITLA.

Convierte todas las variantes de los intents en vectores numéricos (embeddings)
usando sentence-transformers, construye un índice FAISS para búsqueda eficiente
por similitud de coseno, y recupera los top-k intents más similares a la consulta
del usuario.

Pipeline:
  1. Al inicializar: se codifican todas las variantes de la base de conocimiento.
  2. Los vectores se guardan en disco (.cache/embeddings.pkl) para no recalcularlos.
  3. En cada consulta: se codifica la entrada, se normaliza a norma L2 y se busca
     en el índice FAISS usando producto interno (equivalente a similitud de coseno
     después de normalizar).
  4. Se devuelve un diccionario {nombre_intent: puntuación_0-100} con los mejores.

Modelo usado por defecto: paraphrase-multilingual-MiniLM-L12-v2
  - Multilingüe: funciona bien con español e inglés.
  - Compacto (~117 MB): corre en CPU sin necesidad de GPU.
  - Configurable desde config.py sin tocar este archivo.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np

from config import EMBEDDING_MODEL, EMBEDDINGS_CACHE, SEMANTIC_TOP_K
from knowledge_base import INTENTS
from preprocessor import normalize

# ── Estado global del módulo (carga diferida) ─────────────────────────────────
# Se inicializan como None para evitar importar sentence-transformers y FAISS
# hasta que realmente se necesiten. Esto acelera el arranque del bot en modo
# solo-palabras-clave (use_semantic=False).
_model = None          # Instancia de SentenceTransformer; se carga en _load_model()
_index = None          # Índice FAISS de vectores de variantes; se construye en initialize()
_meta: list[str] = []  # Lista paralela al índice: posición i → nombre del intent


# ── Funciones internas ─────────────────────────────────────────────────────────

def _load_model():
    """Carga el modelo de embeddings de forma diferida (solo la primera vez).

    El modelo se importa aquí (no en el nivel de módulo) para evitar que
    sentence-transformers se cargue cuando el chatbot se usa sin semántica.
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        # La primera carga descarga el modelo desde Hugging Face si no está en caché local
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _build_index(embeddings: np.ndarray):
    """Construye el índice FAISS a partir de una matriz de embeddings.

    Usa IndexFlatIP (producto interno exacto). Al normalizar los vectores a norma L2
    antes de insertar, el producto interno es equivalente a la similitud de coseno,
    que mide el ángulo entre vectores independientemente de su magnitud.

    Args:
        embeddings: Matriz float32 de forma (N, D) donde N = número de variantes
                    y D = dimensión del embedding (768 para el modelo por defecto).

    Returns:
        Índice FAISS listo para buscar con search().
    """
    import faiss
    d = embeddings.shape[1]  # Dimensión de cada vector
    index = faiss.IndexFlatIP(d)  # Producto interno (coseno después de normalizar)
    faiss.normalize_L2(embeddings)  # Normalizar a norma 1 para usar coseno como métrica
    index.add(embeddings)           # Insertar todos los vectores en el índice
    return index


def _gather_corpus() -> tuple[list[str], list[str]]:
    """Recopila todas las variantes de la base de conocimiento para indexar.

    Itera sobre todos los intents y sus variantes, normalizando el texto
    para que coincida con la forma en que se codificarán las consultas.

    Returns:
        Tupla (textos, nombres) donde:
          - textos[i]: variante normalizada lista para codificar
          - nombres[i]: nombre del intent al que pertenece esa variante
        Ambas listas tienen el mismo largo y el mismo orden (índice paralelo).
    """
    textos, nombres = [], []
    for intent in INTENTS:
        for variante in intent["variants"]:
            textos.append(normalize(variante))  # Normalizar igual que las consultas
            nombres.append(intent["name"])       # Recordar a qué intent corresponde
    return textos, nombres


def _load_or_build_cache() -> tuple:
    """Carga los embeddings desde el archivo de caché o los calcula si no existe.

    La primera ejecución puede tardar 20-60 segundos dependiendo del hardware
    (codifica cientos de variantes con el modelo de embeddings). Las siguientes
    ejecuciones leen directamente del archivo pickle en milisegundos.

    Returns:
        Tupla (embeddings: np.ndarray, meta: list[str]) con los vectores y
        sus metadatos (nombre del intent por fila).
    """
    ruta_cache = Path(EMBEDDINGS_CACHE)

    # Intentar cargar desde caché para evitar recalcular
    if ruta_cache.exists():
        with open(ruta_cache, "rb") as f:
            cached = pickle.load(f)
        return cached["embeddings"], cached["meta"]

    # Primera vez: codificar todas las variantes y guardar el resultado
    modelo = _load_model()
    textos, nombres = _gather_corpus()
    embeddings = modelo.encode(textos, convert_to_numpy=True, show_progress_bar=True)
    embeddings = embeddings.astype("float32")  # FAISS requiere float32

    # Crear el directorio de caché si no existe y guardar el resultado
    ruta_cache.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_cache, "wb") as f:
        pickle.dump({"embeddings": embeddings, "meta": nombres}, f)

    return embeddings, nombres


# ── API pública ────────────────────────────────────────────────────────────────

def initialize() -> bool:
    """Construye o carga el índice FAISS. Debe llamarse una vez al arrancar.

    Carga los embeddings desde caché (o los genera si es la primera vez),
    luego construye el índice FAISS en memoria para búsquedas rápidas.

    Returns:
        True si la inicialización fue exitosa.
    """
    global _index, _meta
    embeddings, meta = _load_or_build_cache()
    _meta = meta
    # Se pasa una copia para que _build_index pueda normalizar sin alterar la caché
    _index = _build_index(embeddings.copy())
    return True


def search(user_input: str, top_k: int = SEMANTIC_TOP_K) -> dict[str, float]:
    """Busca los intents más similares semánticamente a la consulta del usuario.

    Codifica la entrada, la normaliza a norma L2 y consulta el índice FAISS.
    Para cada intent candidato se conserva solo su puntuación más alta
    (puede aparecer varias veces si múltiples variantes son similares).

    Args:
        user_input: Texto original del usuario (se normalizará internamente).
        top_k:      Número máximo de candidatos a recuperar del índice.
                    Por defecto usa SEMANTIC_TOP_K definido en config.py.

    Returns:
        Diccionario {nombre_intent: puntuación} con valores entre 0 y 100.
        Solo incluye los intents más similares semánticamente (no todos).
        Retorna dict vacío si el índice no está inicializado.

    Ejemplo:
        search("cómo me inscribo")
        → {"inscripcion": 91.4, "oferta_academica": 64.2, "plataforma": 52.8}
    """
    # Si el índice no está cargado, retornar vacío sin lanzar excepción
    if _index is None:
        return {}

    import faiss
    modelo = _load_model()

    # Normalizar la entrada para que coincida con el formato de las variantes indexadas
    entrada_norm = normalize(user_input)

    # Codificar la consulta y normalizar a norma L2 para similitud de coseno
    vector_consulta = modelo.encode([entrada_norm], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(vector_consulta)

    # Buscar top_k*3 para luego poder seleccionar el mejor puntaje por intent
    # (se amplía la búsqueda porque múltiples filas pueden pertenecer al mismo intent)
    distancias, indices = _index.search(vector_consulta, top_k * 3)

    # Agrupar por intent: conservar solo el puntaje más alto para cada uno
    puntuaciones: dict[str, float] = {}
    for dist, idx in zip(distancias[0], indices[0]):
        if idx == -1:
            # FAISS devuelve -1 cuando no hay suficientes resultados en el índice
            continue
        nombre = _meta[idx]
        # Convertir similitud de coseno (0-1) a escala 0-100
        puntuacion = float(dist) * 100
        # Solo guardar si es el mejor puntaje visto para este intent
        if nombre not in puntuaciones or puntuacion > puntuaciones[nombre]:
            puntuaciones[nombre] = round(puntuacion, 2)

    return puntuaciones


def is_ready() -> bool:
    """Indica si el índice semántico está cargado y listo para búsquedas.

    Útil para verificar el estado del motor antes de llamar a search(),
    aunque search() también maneja el caso de índice no inicializado.
    """
    return _index is not None
