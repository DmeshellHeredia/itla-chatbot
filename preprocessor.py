"""
Utilidades de preprocesamiento de texto.

Todas las funciones devuelven texto en minúsculas, sin acentos ni puntuación,
con espacios normalizados. Este formato uniforme garantiza que las comparaciones
entre la entrada del usuario y las palabras clave del bot sean consistentes
independientemente de cómo el usuario escriba su pregunta.

Pipeline de uso típico:
    normalize("¿Cómo me Inscribo?")  → "como me inscribo"
    tokenize("¿Cómo me Inscribo?")   → ["como", "me", "inscribo"]
    normalize_list(["café", "NIÑO"]) → ["cafe", "nino"]

Módulos que dependen de estas utilidades:
    matcher.py        — usa normalize() y tokenize() en cada llamada a match()
    knowledge_base.py — las variantes se preprocesan al arrancar con normalize_list()
"""

import re
import unicodedata


def remove_accents(text: str) -> str:
    """Elimina los signos diacríticos (tildes, diéresis, etc.) de un texto.

    Convierte el texto a la forma de descomposición canónica (NFD) para separar
    cada carácter base de sus marcas de acento, y luego descarta esas marcas.
    Ejemplo: 'café' → 'cafe', 'niño' → 'nino', 'México' → 'Mexico'.
    """
    # NFD separa el carácter base (p.ej. 'e') de su marca de acento ('´')
    normalized = unicodedata.normalize("NFD", text)
    # La categoría 'Mn' (Mark, Nonspacing) agrupa todos los signos diacríticos
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize(text: str) -> str:
    """Aplica el pipeline completo de normalización a un texto.

    Pasos en orden:
      1. Convertir a minúsculas para comparaciones sin distinción de mayúsculas.
      2. Quitar acentos para unificar variantes como 'inscripción' e 'inscripcion'.
      3. Reemplazar puntuación por espacios (se mantienen letras, dígitos y '_').
      4. Colapsar múltiples espacios en uno solo y eliminar espacios extremos.

    Args:
        text: Texto en bruto (entrada del usuario o variante de la base de conocimiento).

    Returns:
        Texto normalizado listo para tokenizar o comparar.
    """
    text = text.lower()
    text = remove_accents(text)
    # [^\w\s] elimina todo excepto letras, dígitos, guión bajo y espacios.
    # El guión bajo se conserva porque \w lo incluye; no afecta al español.
    text = re.sub(r"[^\w\s]", " ", text)
    # Reemplazar secuencias de espacios/tabs/saltos de línea por un solo espacio
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    """Divide el texto en una lista de tokens normalizados.

    Aplica normalize() primero para garantizar que los tokens sean comparables
    con las palabras clave almacenadas en la base de conocimiento.
    El separador es siempre un espacio simple (normalize() garantiza esto).

    Args:
        text: Texto en bruto a tokenizar.

    Returns:
        Lista de palabras normalizadas (sin orden de relevancia).
        Ejemplos:
            tokenize('¿Cómo me Inscribo?') → ['como', 'me', 'inscribo']
            tokenize('café niño')          → ['cafe', 'nino']
            tokenize('')                   → []
    """
    return normalize(text).split()


def normalize_list(phrases: list[str]) -> list[str]:
    """Normaliza una lista completa de frases o palabras clave.

    Atajo conveniente para aplicar normalize() a cada elemento de una lista,
    usado principalmente al preprocesar las variantes e intenciones de la
    base de conocimiento al momento de arrancar el sistema.

    El preprocesamiento en tiempo de carga (en lugar de hacerlo en cada
    consulta) es la principal optimización de rendimiento del motor: evita
    recalcular la normalización de cientos de variantes en cada mensaje del
    usuario.

    Args:
        phrases: Lista de frases en bruto (variantes, palabras clave, etc.).

    Returns:
        Lista con cada frase ya normalizada en el mismo orden.
    """
    return [normalize(p) for p in phrases]
