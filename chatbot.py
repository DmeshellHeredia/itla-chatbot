"""
Motor principal del chatbot del ITLA.

Orquesta el pipeline completo de coincidencia de intenciones:
  1. Coincidencia exacta por palabras clave / coincidencia difusa (fuzzy)
  2. Búsqueda semántica mediante embeddings (si el motor está disponible)
  3. Enrutamiento por nivel de confianza (alto / medio / bajo)
  4. Respuesta de respaldo (fallback) si ningún método produce resultado

Uso básico:
    bot = ChatBot()          # carga el motor semántico si está disponible
    respuesta, nivel = bot.respond("¿Cómo me inscribo?")
    # nivel puede ser: "high" | "medium" | "low" | "fallback"

Para desactivar el motor semántico (más rápido, menos preciso):
    bot = ChatBot(use_semantic=False)
"""

from __future__ import annotations

import random

import matcher
import semantic
from config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM
from knowledge_base import INTENTS

# ── Banco de mensajes de respaldo ─────────────────────────────────────────────
# Se usan cuando el chatbot no logra identificar la intención del usuario.
# Tener tres mensajes distintos y elegir uno al azar cumple dos propósitos:
#   1. Evita que el bot suene repetitivo en conversaciones largas.
#   2. Cada mensaje ofrece una salida diferente (lista de temas, correo, sitio web)
#      para aumentar las chances de que el usuario encuentre lo que busca.

_FALLBACK_NOT_UNDERSTOOD = [
    (
        "No entendí tu pregunta. 🤔\n\n"
        "Puedo ayudarte con:\n"
        "- 📚 Oferta académica\n"
        "- 📝 Inscripción\n"
        "- 📍 Ubicación y sedes\n"
        "- 📞 Contacto\n"
        "- 💻 Plataforma virtual\n\n"
        "¿Sobre cuál de estos temas tienes dudas?"
    ),
    (
        "No pude encontrar una respuesta para eso. 😕\n\n"
        "Intenta preguntar de otra forma, o escribe directamente al ITLA:\n"
        "📧 info@itla.edu.do | 📞 (809) 530-4852"
    ),
    (
        "Esa pregunta está fuera de mi alcance por ahora. 🙏\n\n"
        "Para consultas específicas, visita [itla.edu.do](https://www.itla.edu.do) "
        "o contacta a admisiones."
    ),
]

# Prefijo que se antepone a las respuestas de baja confianza para advertir al
# usuario que la respuesta podría no ser exactamente lo que busca.
_FALLBACK_LOW_CONFIDENCE_PREFIX = (
    "No estoy del todo seguro, pero esto podría ayudarte:\n\n"
)

# Temas sugeridos que se muestran al final de respuestas de baja confianza
# para guiar al usuario hacia preguntas que el bot puede responder mejor.
_SUGGESTED_TOPICS = [
    "oferta académica", "inscripción", "sedes", "plataforma",
    "contacto", "educación continua", "soporte", "becas",
]


def _build_low_confidence_response(intent: dict) -> str:
    """Construye la respuesta para coincidencias de baja confianza.

    Usa el texto extendido del intent si existe, y añade una sugerencia
    aleatoria de tema para invitar al usuario a seguir explorando.
    """
    # Preferir la respuesta extendida cuando esté disponible; si no, usar la corta
    body = intent.get("extended") or intent["response"]
    # Elegir un tema al azar como sugerencia al final del mensaje
    topic_hint = random.choice(_SUGGESTED_TOPICS)
    return (
        f"{_FALLBACK_LOW_CONFIDENCE_PREFIX}{body}\n\n"
        f"---\n*¿Esto responde tu pregunta? También puedes preguntar sobre **{topic_hint}**.*"
    )


# ── API pública ───────────────────────────────────────────────────────────────

class ChatBot:
    """Chatbot del ITLA basado en intenciones con soporte semántico opcional.

    Atributos:
        use_semantic: Si es True, intenta cargar el motor semántico al iniciar.
        _semantic_ready: Indica si el motor semántico se cargó correctamente.
    """

    def __init__(self, use_semantic: bool = True):
        self.use_semantic = use_semantic
        # Empieza como False; se actualiza a True solo si la carga es exitosa
        self._semantic_ready = False

        if use_semantic:
            try:
                # Carga el modelo de embeddings; puede tardar varios segundos
                self._semantic_ready = semantic.initialize()
                print("✅ Motor semántico listo.")
            except Exception as e:
                # Si falla (sin GPU, modelo ausente, etc.) el bot sigue funcionando
                # usando solo coincidencia por palabras clave y fuzzy matching
                print(f"⚠️  Motor semántico no disponible: {e}")

    def respond(self, user_input: str) -> tuple[str, str]:
        """Procesa la entrada del usuario y devuelve la respuesta apropiada.

        Pipeline de decisión:
          1. Valida que la entrada no esté vacía.
          2. Obtiene puntuaciones semánticas (si el motor está activo).
          3. Llama al matcher para encontrar la intención más probable.
          4. Enruta la respuesta según el nivel de confianza obtenido.

        Args:
            user_input: Texto escrito por el usuario en el chat.

        Returns:
            Tupla (texto_de_respuesta, etiqueta_de_confianza).
            etiqueta_de_confianza puede ser: "high" | "medium" | "low" | "fallback"
        """
        user_input = user_input.strip()

        # Entrada vacía: pedir al usuario que escriba su pregunta
        if not user_input:
            return "Escribe tu pregunta y te ayudo. 😊", "fallback"

        # ── Paso 1: Puntuaciones semánticas (capa opcional) ───────────────────
        # Se genera un diccionario {nombre_intent: puntuación} con embeddings.
        # Si el motor no está disponible, se usa un dict vacío y el matcher
        # depende únicamente de palabras clave y fuzzy matching.
        sem_scores = {}
        if self.use_semantic and self._semantic_ready:
            try:
                sem_scores = semantic.search(user_input)
            except Exception:
                # Ignorar errores en tiempo de ejecución del motor semántico
                pass

        # ── Paso 2: Coincidencia de intención ────────────────────────────────
        # El matcher combina puntuaciones de palabras clave, fuzzy y semántica
        # para elegir la intención más probable y calcular su puntuación total.
        result = matcher.match(user_input, sem_scores)

        # Si ningún intent supera el umbral mínimo, retornar mensaje de respaldo
        if result is None:
            return random.choice(_FALLBACK_NOT_UNDERSTOOD), "fallback"

        intent = result["intent"]
        score  = result["score"]
        # Convierte la puntuación numérica a etiqueta legible ("high"/"medium"/"low")
        level  = matcher.confidence_label(score)

        # ── Paso 3: Enrutamiento por nivel de confianza ───────────────────────

        # Confianza alta: respuesta corta y directa
        if level == "high":
            return intent["response"], "high"

        # Confianza media: respuesta extendida para dar más contexto al usuario
        if level == "medium":
            response = intent.get("extended") or intent["response"]
            return response, "medium"

        # Confianza baja: respuesta extendida con advertencia y sugerencia de tema
        return _build_low_confidence_response(intent), "low"

    def list_intents(self) -> list[str]:
        """Devuelve la lista de nombres de todas las intenciones registradas.

        Útil para depuración, pruebas o para generar menús de temas disponibles
        sin necesidad de importar knowledge_base directamente.

        Returns:
            Lista de strings con los 'name' de cada intent en el mismo orden
            en que aparecen en INTENTS (orden de definición en knowledge_base.py).

        Ejemplo:
            bot.list_intents()
            → ['saludo', 'que_es_itla', 'ubicacion', 'telefono', ...]
        """
        return [i["name"] for i in INTENTS]
