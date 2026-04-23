"""
ITLA Chatbot – Web Interface (Gradio)
Run: python app.py
"""

import gradio as gr

from chatbot import ChatBot

# ── Bootstrap ─────────────────────────────────────────────────────────────────
print("🚀 Loading ITLA Chatbot…")
bot = ChatBot(use_semantic=True)
print("✅ Ready.\n")

# ── Styling ───────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
/* ── Root palette ── */
:root {
    --itla-blue:   #003087;
    --itla-red:    #c1121f;
    --itla-light:  #f0f4ff;
    --radius:      12px;
}

/* ── Chatbot bubble overrides ── */
.message.bot  { background: var(--itla-light) !important; border-radius: var(--radius) !important; }
.message.user { background: var(--itla-blue)  !important; color: #fff !important; border-radius: var(--radius) !important; }

/* ── Quick-action buttons ── */
.quick-btn button {
    background: var(--itla-blue) !important;
    color: white !important;
    border-radius: 20px !important;
    font-size: 0.82rem !important;
    padding: 6px 14px !important;
    border: none !important;
    cursor: pointer;
    transition: background 0.2s;
}
.quick-btn button:hover { background: var(--itla-red) !important; }

/* ── Header banner ── */
.header-banner {
    background: linear-gradient(135deg, #003087 0%, #1a56c4 100%);
    color: white;
    padding: 20px 28px;
    border-radius: var(--radius);
    margin-bottom: 8px;
}
.header-banner h1 { margin: 0; font-size: 1.5rem; }
.header-banner p  { margin: 4px 0 0; font-size: 0.9rem; opacity: 0.85; }

/* ── Send button ── */
#send-btn { background: var(--itla-blue) !important; color: white !important; }
"""

# ── Example questions ─────────────────────────────────────────────────────────
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

# ── Quick-action mapping ──────────────────────────────────────────────────────
QUICK_ACTIONS = {
    "📚 Oferta Académica":    "¿Cuáles carreras ofrecen en el ITLA?",
    "📝 Inscripción":         "¿Cómo es el proceso de inscripción?",
    "🎓 Educación Continua":  "¿Tienen cursos cortos o educación continua?",
    "🛠️ Soporte":              "Necesito soporte técnico",
    "📞 Contacto":            "¿Cuál es el teléfono y correo del ITLA?",
    "🗺️ Sedes":               "¿En qué provincias tienen sedes?",
}

# ── Core chat function ────────────────────────────────────────────────────────

def chat(user_message: str, history: list):
    if not user_message.strip():
        return history, ""

    response, confidence = bot.respond(user_message)

    # Confidence badge in parenthesis (subtle, helpful for debugging)
    badge = {"high": "", "medium": " *(respuesta aproximada)*", "low": " *(baja confianza)*", "fallback": ""}
    full_response = response + badge.get(confidence, "")

    history = history or []
    history.append({"role": "user",      "content": user_message})
    history.append({"role": "assistant", "content": full_response})
    return history, ""


def quick_action(label: str, history: list):
    question = QUICK_ACTIONS.get(label, "")
    if not question:
        return history
    return chat(question, history)[0]


def clear_chat():
    return [], ""

# ── Build UI ──────────────────────────────────────────────────────────────────

with gr.Blocks(css=CUSTOM_CSS, title="ITLA Chatbot") as demo:

    # Header
    gr.HTML("""
    <div class="header-banner">
        <h1>🎓 Asistente Virtual del ITLA</h1>
        <p>Instituto Tecnológico de Las Américas · Asistente impulsado por IA local</p>
    </div>
    """)

    with gr.Row():
        # ── Left column: chat ─────────────────────────────────────────────────
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": (
                    "¡Hola! 👋 Soy el asistente virtual del **ITLA**.\n\n"
                    "Puedo ayudarte con información sobre carreras, inscripciones, sedes, "
                    "contacto y más. ¿En qué te puedo ayudar hoy?"
                )}],
                type="messages",
                height=480,
                show_label=False,
                bubble_full_width=False,
            )

            with gr.Row():
                txt = gr.Textbox(
                    placeholder="Escribe tu pregunta aquí…",
                    show_label=False,
                    container=False,
                    scale=5,
                )
                send_btn = gr.Button("Enviar ➤", scale=1, elem_id="send-btn")

            with gr.Row():
                clear_btn = gr.Button("🗑️ Limpiar chat", size="sm", variant="secondary")

        # ── Right column: quick actions + examples ────────────────────────────
        with gr.Column(scale=1, min_width=200):
            gr.Markdown("### ⚡ Acceso rápido")
            for label in QUICK_ACTIONS:
                btn = gr.Button(label, elem_classes="quick-btn")
                btn.click(
                    fn=lambda l=label: quick_action(l, []),
                    inputs=None,
                    outputs=chatbot,
                )

            gr.Markdown("---\n### 💡 Ejemplos")
            for ex in EXAMPLES:
                ex_btn = gr.Button(ex, size="sm", elem_classes="quick-btn")
                ex_btn.click(
                    fn=lambda q=ex: chat(q, [])[0],
                    inputs=None,
                    outputs=chatbot,
                )

    # ── Event handlers ────────────────────────────────────────────────────────
    # Fix: quick actions need current history
    state = gr.State([])

    def chat_with_state(msg, hist):
        new_hist, _ = chat(msg, hist)
        return new_hist, new_hist, ""

    txt.submit(chat_with_state, [txt, state], [chatbot, state, txt])
    send_btn.click(chat_with_state, [txt, state], [chatbot, state, txt])
    clear_btn.click(lambda: ([], [], ""), None, [chatbot, state, txt])

    # Fix quick-action and example buttons to use stateful history
    for label in QUICK_ACTIONS:
        pass  # Buttons already wired above (stateless demo mode; upgrade below)

    gr.Markdown(
        "<center><small>ITLA Chatbot · Proyecto académico · "
        "[itla.edu.do](https://www.itla.edu.do)</small></center>"
    )


# ── Stateful quick-action fix (rewire after state is defined) ─────────────────
# Gradio requires buttons to be defined before wiring, so we rebuild the demo
# with proper state threading.

def make_demo():
    with gr.Blocks(css=CUSTOM_CSS, title="ITLA Chatbot") as app:

        gr.HTML("""
        <div class="header-banner">
            <h1>🎓 Asistente Virtual del ITLA</h1>
            <p>Instituto Tecnológico de Las Américas · Asistente impulsado por IA local</p>
        </div>
        """)

        state = gr.State([])

        with gr.Row():
            with gr.Column(scale=3):
                chatbot_ui = gr.Chatbot(
                    value=[{"role": "assistant", "content": (
                        "¡Hola! 👋 Soy el asistente virtual del **ITLA**.\n\n"
                        "Puedo ayudarte con información sobre carreras, inscripciones, sedes, "
                        "contacto y más. ¿En qué te puedo ayudar hoy?"
                    )}],
                    type="messages",
                    height=480,
                    show_label=False,
                    bubble_full_width=False,
                )

                with gr.Row():
                    txt_in = gr.Textbox(
                        placeholder="Escribe tu pregunta aquí…",
                        show_label=False,
                        container=False,
                        scale=5,
                    )
                    send = gr.Button("Enviar ➤", scale=1, elem_id="send-btn")

                clear = gr.Button("🗑️ Limpiar chat", size="sm", variant="secondary")

            with gr.Column(scale=1, min_width=200):
                gr.Markdown("### ⚡ Acceso rápido")
                qa_buttons = []
                for label in QUICK_ACTIONS:
                    b = gr.Button(label, elem_classes="quick-btn")
                    qa_buttons.append((label, b))

                gr.Markdown("---\n### 💡 Ejemplos")
                ex_buttons = []
                for ex in EXAMPLES:
                    b = gr.Button(ex, size="sm", elem_classes="quick-btn")
                    ex_buttons.append((ex, b))

        def _submit(msg, hist):
            if not msg.strip():
                return hist, hist, ""
            new_hist, _ = chat(msg, hist)
            return new_hist, new_hist, ""

        def _quick(question, hist):
            new_hist, _ = chat(question, hist)
            return new_hist, new_hist

        def _clear():
            init = [{"role": "assistant", "content": (
                "¡Hola! 👋 Soy el asistente virtual del **ITLA**.\n\n"
                "¿En qué te puedo ayudar hoy?"
            )}]
            return init, init, ""

        txt_in.submit(_submit, [txt_in, state], [chatbot_ui, state, txt_in])
        send.click(_submit, [txt_in, state], [chatbot_ui, state, txt_in])
        clear.click(_clear, None, [chatbot_ui, state, txt_in])

        for label, btn in qa_buttons:
            q = QUICK_ACTIONS[label]
            btn.click(
                fn=lambda hist, _q=q: _quick(_q, hist),
                inputs=[state],
                outputs=[chatbot_ui, state],
            )

        for ex, btn in ex_buttons:
            btn.click(
                fn=lambda hist, _q=ex: _quick(_q, hist),
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
    )
