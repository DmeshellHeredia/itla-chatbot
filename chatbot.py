"""
Core chatbot engine.

Orchestrates the full matching pipeline:
  exact keyword/fuzzy  →  semantic (if ready)  →  confidence routing  →  fallback
"""

from __future__ import annotations

import random

import matcher
import semantic
from config import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM
from knowledge_base import INTENTS

# ── Fallback message banks ────────────────────────────────────────────────────

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

_FALLBACK_LOW_CONFIDENCE_PREFIX = (
    "No estoy del todo seguro, pero esto podría ayudarte:\n\n"
)

_SUGGESTED_TOPICS = [
    "oferta académica", "inscripción", "sedes", "plataforma",
    "contacto", "educación continua", "soporte", "becas",
]


def _build_low_confidence_response(intent: dict) -> str:
    body = intent.get("extended") or intent["response"]
    topic_hint = random.choice(_SUGGESTED_TOPICS)
    return (
        f"{_FALLBACK_LOW_CONFIDENCE_PREFIX}{body}\n\n"
        f"---\n*¿Esto responde tu pregunta? También puedes preguntar sobre **{topic_hint}**.*"
    )


# ── Public API ────────────────────────────────────────────────────────────────

class ChatBot:
    def __init__(self, use_semantic: bool = True):
        self.use_semantic = use_semantic
        self._semantic_ready = False

        if use_semantic:
            try:
                self._semantic_ready = semantic.initialize()
                print("✅ Semantic engine ready.")
            except Exception as e:
                print(f"⚠️  Semantic engine unavailable: {e}")

    def respond(self, user_input: str) -> tuple[str, str]:
        """
        Process user input and return (response_text, confidence_label).

        confidence_label: "high" | "medium" | "low" | "fallback"
        """
        user_input = user_input.strip()
        if not user_input:
            return "Escribe tu pregunta y te ayudo. 😊", "fallback"

        # ── Semantic scores (optional layer) ──────────────────────────────────
        sem_scores = {}
        if self.use_semantic and self._semantic_ready:
            try:
                sem_scores = semantic.search(user_input)
            except Exception:
                pass

        # ── Match ─────────────────────────────────────────────────────────────
        result = matcher.match(user_input, sem_scores)

        if result is None:
            return random.choice(_FALLBACK_NOT_UNDERSTOOD), "fallback"

        intent = result["intent"]
        score  = result["score"]
        level  = matcher.confidence_label(score)

        if level == "high":
            return intent["response"], "high"

        if level == "medium":
            response = intent.get("extended") or intent["response"]
            return response, "medium"

        # low confidence
        return _build_low_confidence_response(intent), "low"

    def list_intents(self) -> list[str]:
        return [i["name"] for i in INTENTS]
