"""
Suite de pruebas del pipeline de coincidencia del chatbot ITLA.

Verifica que el motor de matching (palabras clave + fuzzy) reconozca
correctamente las intenciones del usuario en distintos escenarios:
  - Consultas exactas y limpias
  - Consultas con errores tipográficos o lenguaje informal
  - Consultas muy cortas (una o dos palabras)
  - Consultas largas y naturales
  - Consultas fuera del dominio (deben NO matchear ningún intent específico)

Uso:
    python test_chatbot.py

El modo semántico se desactiva (use_semantic=False) para que las pruebas
sean rápidas y reproducibles sin depender del motor FAISS.

Criterio de éxito:
  - Consultas con intent esperado: el nombre del intent debe coincidir exactamente.
  - Consultas fuera del dominio (expected=None): el resultado debe ser None
    o tener una puntuación menor a 35 (confianza baja).
"""

import sys
from chatbot import ChatBot

# Inicializar el bot sin motor semántico para tests rápidos y deterministas
bot = ChatBot(use_semantic=False)

# ── Casos de prueba: (entrada_usuario, nombre_intent_esperado_o_None) ──────────
# Cada tupla representa un escenario y el resultado que se espera del matcher.
# None como intent esperado significa "fuera del dominio" (sin coincidencia clara).
TESTS = [
    # ── Consultas exactas / bien escritas ─────────────────────────────────────
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

    # ── Consultas con errores tipográficos o lenguaje informal ────────────────
    # Prueban la tolerancia del motor fuzzy a errores de 1-2 caracteres.
    # Cada caso cubre un tipo de error distinto para validar la robustez del motor:
    ("hola komo estas",               "saludo"),         # 'k' por 'c'  — sustitución fonética común
    ("donde kedan ubicados",          "ubicacion"),      # 'k' por 'qu' — variante ortográfica informal
    ("cuales careras tienen",         "oferta_academica"), # 'rr' → 'r'  — reducción de consonante doble
    ("como me yncribo",               "inscripcion"),    # 'y' por 'i'  — confusión fonética
    ("tlefono del itla",              "telefono"),       # vocal inicial omitida — error de mecanografía

    # ── Consultas muy cortas (1-2 palabras) ───────────────────────────────────
    # Verifican que keywords de alto peso activen el intent correcto
    ("itla",                          "que_es_itla"),
    ("carreras",                      "oferta_academica"),
    ("sedes",                         "sedes"),
    ("correo",                        "correo"),

    # ── Consultas largas y naturales ──────────────────────────────────────────
    # Simulan cómo un usuario real formularía su pregunta en lenguaje coloquial
    ("quiero saber más sobre cómo inscribirme en el itla este semestre", "inscripcion"),
    ("estoy interesado en estudiar desarrollo de software en el itla",   "oferta_academica"),
    ("cómo puedo recuperar mi usuario para entrar al campus virtual",    "plataforma"),
    ("tienen algún programa de certificación en cisco o comptia",        "educacion_continua"),

    # ── Consultas fuera del dominio (deben NO dar coincidencia clara) ─────────
    # El bot no debe responder con confianza sobre temas ajenos al ITLA.
    # Se acepta resultado=None O puntaje < 35 (umbral CONFIDENCE_MEDIUM de config.py).
    # Si el motor asignara puntaje alto aquí, indicaría falsos positivos graves.
    ("cuánto cuesta un iPhone",       None),  # tecnología de consumo — sin relación con ITLA
    ("quién ganó el mundial",         None),  # deporte — completamente fuera del dominio
]


# ── Función de ejecución de la suite ──────────────────────────────────────────

def run():
    """Ejecuta todos los casos de prueba e imprime un reporte detallado.

    Para cada caso muestra: entrada, intent esperado, intent obtenido,
    puntuación de confianza y si la prueba pasó o falló.
    Termina con código de salida 1 si alguna prueba falla (útil para CI).
    """
    import matcher

    pasadas, falladas = 0, 0

    # Encabezado de la tabla de resultados
    print(f"{'ENTRADA':<55} {'ESPERADO':<25} {'OBTENIDO':<25} {'PUNTUACIÓN':>10}  RESULTADO")
    print("─" * 125)

    for entrada_usuario, esperado in TESTS:
        resultado = matcher.match(entrada_usuario)

        # Extraer nombre e intent del resultado (None si no superó el umbral mínimo)
        nombre_obtenido = resultado["intent"]["name"] if resultado else None
        puntuacion      = resultado["score"] if resultado else 0

        if esperado is None:
            # Caso fuera del dominio: se acepta sin coincidencia o con baja confianza
            ok    = (resultado is None) or (puntuacion < 35)
            marca = "✅" if ok else "⚠️ "
        else:
            # Caso con intent definido: debe coincidir exactamente con el esperado
            ok    = (nombre_obtenido == esperado)
            marca = "✅" if ok else "❌"

        if ok:
            pasadas += 1
        else:
            falladas += 1

        print(f"{entrada_usuario:<55} {str(esperado):<25} {str(nombre_obtenido):<25} {puntuacion:>10.1f}  {marca}")

    # Línea separadora y resumen final
    print("─" * 125)
    total = len(TESTS)
    print(f"\nResultados: {pasadas}/{total} pasadas  |  {falladas} falladas")

    # Salir con error si alguna prueba falló (compatibilidad con pipelines CI)
    if falladas > 0:
        sys.exit(1)


if __name__ == "__main__":
    run()
