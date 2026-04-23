"""
ITLA Chatbot – Web Interface (Gradio)
Compatible with newer Gradio message-format chat history.
Run: python app.py
"""

import gradio as gr

from chatbot import ChatBot

# ── Bootstrap ─────────────────────────────────────────────────────────────────
print("🚀 Loading ITLA Chatbot…")
bot = ChatBot(use_semantic=True)
print("✅ Ready.\n")

# ── Constants ─────────────────────────────────────────────────────────────────
_INITIAL_MSG = (
    "¡Hola! 👋 Soy el asistente virtual del **ITLA**.\n\n"
    "Puedo ayudarte con información sobre carreras, inscripciones, sedes, "
    "contacto y más. ¿En qué te puedo ayudar hoy?"
)

_CONFIDENCE_BADGES = {
    "high": "",
    "medium": " *(respuesta aproximada)*",
    "low": " *(baja confianza)*",
    "fallback": "",
}

# ── Styling ───────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
:root {
    --itla-blue:  #003087;
    --itla-red:   #c1121f;
    --itla-light: #f0f4ff;
    --radius:     12px;
}
.header-banner {
    background: linear-gradient(135deg, #003087 0%, #1a56c4 100%);
    color: white;
    padding: 20px 28px;
    border-radius: var(--radius);
    margin-bottom: 8px;
}
.header-banner h1 { margin: 0; font-size: 1.5rem; }
.header-banner p  { margin: 4px 0 0; font-size: 0.9rem; opacity: 0.85; }
.quick-btn button {
    background: var(--itla-blue) !important;
    color: white !important;
    border-radius: 20px !important;
    font-size: 0.82rem !important;
    padding: 6px 14px !important;
    border: none !important;
    transition: background 0.2s;
}
.quick-btn button:hover { background: var(--itla-red) !important; }
#send-btn { background: var(--itla-blue) !important; color: white !important; }
"""

# ── Quick-action questions ────────────────────────────────────────────────────
QUICK_ACTIONS = {
    "📚 Oferta Académica": "¿Cuáles carreras ofrecen en el ITLA?",
    "📝 Inscripción": "¿Cómo es el proceso de inscripción?",
    "🎓 Educación Continua": "¿Tienen cursos cortos o educación continua?",
    "🛠️ Soporte": "Necesito soporte técnico",
    "📞 Contacto": "¿Cuál es el teléfono y correo del ITLA?",
    "🗺️ Sedes": "¿En qué provincias tienen sedes?",
}

EXAMPLES = [
    "¿Qué es el ITLA?",
    "¿Cuáles carreras ofrecen?",
    "¿Cómo me inscribo?",
    "¿Dónde están ubicados?",
    "¿Tienen cursos cortos?",
    "¿Cuál es el teléfono del ITLA?",
    "¿Cómo accedo a la plataforma?",
    "¿Hay becas disponibles?",
]


def _assistant_message(text: str) -> dict:
    return {"role": "assistant", "content": text}


def _user_message(text: str) -> dict:
    return {"role": "user", "content": text}


# ── Chat logic ────────────────────────────────────────────────────────────────
def _respond(user_msg: str, history: list) -> tuple[list, str]:
    user_msg = user_msg.strip()
    if not user_msg:
        return history, ""

    response, confidence = bot.respond(user_msg)
    badge = _CONFIDENCE_BADGES.get(confidence, "")
    bot_msg = response + badge

    history = list(history or [])
    history.append(_user_message(user_msg))
    history.append(_assistant_message(bot_msg))
    return history, ""


def _quick(question: str, history: list) -> tuple[list, list]:
    new_history, _ = _respond(question, history)
    return new_history, new_history


# ── Build UI ──────────────────────────────────────────────────────────────────
def make_demo() -> gr.Blocks:
    with gr.Blocks(title="ITLA Chatbot") as app:
        gr.HTML(
            """
        <div class="header-banner">
            <h1>🎓 Asistente Virtual del ITLA</h1>
            <p>Instituto Tecnológico de Las Américas · Asistente impulsado por IA local</p>
        </div>
        """
        )

        initial_history = [_assistant_message(_INITIAL_MSG)]
        state = gr.State(initial_history)

        with gr.Row():
            with gr.Column(scale=3):
                chatbot_ui = gr.Chatbot(
                    value=initial_history,
                    height=480,
                    show_label=False,
                )

                with gr.Row():
                    txt_in = gr.Textbox(
                        placeholder="Escribe tu pregunta aquí…",
                        show_label=False,
                        container=False,
                        scale=5,
                    )
                    send_btn = gr.Button("Enviar ➤", scale=1, elem_id="send-btn")

                clear_btn = gr.Button("🗑️ Limpiar chat", size="sm", variant="secondary")

            with gr.Column(scale=1, min_width=200):
                gr.Markdown("### ⚡ Acceso rápido")
                qa_buttons = []
                for label in QUICK_ACTIONS:
                    button = gr.Button(label, elem_classes="quick-btn")
                    qa_buttons.append((label, button))

                gr.Markdown("---\n### 💡 Ejemplos")
                ex_buttons = []
                for ex in EXAMPLES:
                    button = gr.Button(ex, size="sm", elem_classes="quick-btn")
                    ex_buttons.append((ex, button))

        def _submit(msg, hist):
            new_hist, cleared = _respond(msg, hist)
            return new_hist, new_hist, cleared

        def _do_clear():
            init = [_assistant_message(_INITIAL_MSG)]
            return init, init, ""

        txt_in.submit(_submit, [txt_in, state], [chatbot_ui, state, txt_in])
        send_btn.click(_submit, [txt_in, state], [chatbot_ui, state, txt_in])
        clear_btn.click(_do_clear, None, [chatbot_ui, state, txt_in])

        for label, btn in qa_buttons:
            question = QUICK_ACTIONS[label]
            btn.click(
                fn=lambda hist, q=question: _quick(q, hist),
                inputs=[state],
                outputs=[chatbot_ui, state],
            )

        for ex, btn in ex_buttons:
            btn.click(
                fn=lambda hist, q=ex: _quick(q, hist),
                inputs=[state],
                outputs=[chatbot_ui, state],
            )

        gr.Markdown(
            "<center><small>ITLA Chatbot · Proyecto académico · "
            "[itla.edu.do](https://www.itla.edu.do)</small></center>"
        )

    return app


if __name__ == "__main__":
    app = make_demo()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        css=CUSTOM_CSS,
    )