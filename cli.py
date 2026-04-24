"""
Interfaz de línea de comandos (CLI) del chatbot del ITLA.

Mantiene el bucle de conversación sin dependencias de interfaz gráfica.
Útil para pruebas rápidas, entornos sin navegador o depuración del motor.

Uso:
    python cli.py

Flujo de ejecución:
    1. Inicializa el ChatBot (carga el motor semántico si está disponible).
    2. Lee mensajes del usuario en un bucle hasta que escriba una palabra clave de salida.
    3. Imprime la respuesta junto con el nivel de confianza entre corchetes.

Palabras clave de salida: 'salir', 'exit', 'quit', 'bye'
"""

from chatbot import ChatBot

# Mensaje de bienvenida al iniciar la sesión de CLI
print("🎓 ITLA Chatbot (CLI) · Escribe 'salir' para terminar\n")

# Se inicializa el chatbot con búsqueda semántica activada para
# obtener respuestas más precisas basadas en similitud de significado
bot = ChatBot(use_semantic=True)

# Bucle principal de conversación: continúa hasta que el usuario decida salir
while True:
    try:
        # Leer la entrada del usuario y eliminar espacios en blanco sobrantes
        user_input = input("Tú: ").strip()
    except (EOFError, KeyboardInterrupt):
        # Manejar cierre abrupto (Ctrl+C o fin de entrada estándar)
        print("\nBot: ¡Hasta luego! 👋")
        break

    # Verificar si el usuario escribió alguna de las palabras clave de salida
    if user_input.lower() in {"salir", "exit", "quit", "bye"}:
        print("Bot: ¡Hasta luego! 👋")
        break

    # Ignorar mensajes vacíos y volver a pedir entrada
    if not user_input:
        continue

    # Obtener la respuesta del chatbot junto con el nivel de confianza
    response, confidence = bot.respond(user_input)

    # Mostrar la respuesta indicando el nivel de confianza entre corchetes
    print(f"Bot [{confidence}]: {response}\n")
