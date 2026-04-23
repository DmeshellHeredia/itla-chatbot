"""
CLI interface – preserves the original chatbot loop.
Run: python cli.py
"""

from chatbot import ChatBot

print("🎓 ITLA Chatbot (CLI) · Escribe 'salir' para terminar\n")
bot = ChatBot(use_semantic=True)

while True:
    try:
        user_input = input("Tú: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nBot: ¡Hasta luego! 👋")
        break

    if user_input.lower() in {"salir", "exit", "quit", "bye"}:
        print("Bot: ¡Hasta luego! 👋")
        break

    if not user_input:
        continue

    response, confidence = bot.respond(user_input)
    print(f"Bot [{confidence}]: {response}\n")
