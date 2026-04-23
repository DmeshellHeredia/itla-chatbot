"""
Test suite for the ITLA chatbot matching pipeline.
Run: python test_chatbot.py
"""

import sys
from chatbot import ChatBot

bot = ChatBot(use_semantic=False)  # Fast mode (no semantic) for unit tests

# ── Test cases: (input, expected_intent_name_or_None) ─────────────────────────
TESTS = [
    # Exact / clean queries
    ("hola",                          "saludo"),
    ("qué es el itla",                "que_es_itla"),
    ("dónde están ubicados",          "ubicacion"),
    ("cuál es el teléfono",           "telefono"),
    ("cuál es el correo del itla",    "correo"),
    ("qué carreras ofrecen",          "oferta_academica"),
    ("cómo me inscribo",              "inscripcion"),
    ("tienen cursos cortos",          "educacion_continua"),
    ("necesito soporte técnico",      "soporte"),
    ("cuántas sedes tienen",          "sedes"),
    ("cómo accedo a la plataforma",   "plataforma"),
    ("hay becas disponibles",         "costos_becas"),
    ("adiós gracias",                 "despedida"),

    # Misspelled / informal
    ("hola komo estas",               "saludo"),
    ("donde kedan ubicados",          "ubicacion"),
    ("cuales careras tienen",         "oferta_academica"),
    ("como me yncribo",               "inscripcion"),
    ("tlefono del itla",              "telefono"),

    # Short queries
    ("itla",                          "que_es_itla"),
    ("carreras",                      "oferta_academica"),
    ("sedes",                         "sedes"),
    ("correo",                        "correo"),

    # Long / natural queries
    ("quiero saber más sobre cómo inscribirme en el itla este semestre", "inscripcion"),
    ("estoy interesado en estudiar desarrollo de software en el itla",   "oferta_academica"),
    ("cómo puedo recuperar mi usuario para entrar al campus virtual",    "plataforma"),
    ("tienen algún programa de certificación en cisco o comptia",        "educacion_continua"),

    # Out-of-domain (should NOT match a specific intent cleanly)
    ("cuánto cuesta un iPhone",       None),
    ("quién ganó el mundial",         None),
]

# ── Runner ─────────────────────────────────────────────────────────────────────

def run():
    import matcher

    passed, failed, skipped = 0, 0, 0
    print(f"{'INPUT':<55} {'EXPECTED':<25} {'GOT':<25} {'SCORE':>6}  PASS?")
    print("─" * 120)

    for user_input, expected in TESTS:
        result = matcher.match(user_input)

        got_name  = result["intent"]["name"] if result else None
        got_score = result["score"] if result else 0

        if expected is None:
            # We just want low/no confidence
            ok = (result is None) or (got_score < 35)
            label = "✅" if ok else "⚠️ "
            if ok:
                passed += 1
            else:
                failed += 1
        else:
            ok = (got_name == expected)
            label = "✅" if ok else "❌"
            if ok:
                passed += 1
            else:
                failed += 1

        print(f"{user_input:<55} {str(expected):<25} {str(got_name):<25} {got_score:>6.1f}  {label}")

    print("─" * 120)
    total = len(TESTS)
    print(f"\nResults: {passed}/{total} passed  |  {failed} failed")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run()
