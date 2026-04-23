"""
ITLA Chatbot — Web Interface

Compatibility:
  - No `type=` on gr.Chatbot
  - No `bubble_full_width`, `show_share_button`, `show_copy_button`, `avatar_images`
  - No `show_api` in launch()
  - Chat history: {"role": "...", "content": "..."} dict format
  - CSS passed to launch(), not Blocks()
  - demo.queue() for streaming/generator support

Run: python app.py
"""

from __future__ import annotations

import threading

import gradio as gr

from chatbot import ChatBot

# ── Background loading ─────────────────────────────────────────────────────────
_bot: ChatBot | None = None
_bot_ready = threading.Event()


def _load():
    global _bot
    _bot = ChatBot(use_semantic=True)
    _bot_ready.set()


threading.Thread(target=_load, daemon=True).start()

# ── Constants ──────────────────────────────────────────────────────────────────
_INITIAL_MSG = (
    "¡Hola! 👋 Soy el asistente virtual del **ITLA**.\n\n"
    "Puedo ayudarte con información sobre:\n"
    "- 📚 Oferta académica y carreras\n"
    "- 📝 Inscripción y admisión\n"
    "- 📍 Ubicación y sedes\n"
    "- 📞 Contacto\n"
    "- 💻 Plataforma virtual\n\n"
    "¿En qué te puedo ayudar hoy?"
)

_LOADING_MSG = (
    "⏳ *Iniciando el motor de IA por primera vez...* "
    "Esto puede tomar 20–30 segundos. Solo ocurre la primera vez."
)

_CONFIDENCE_BADGES = {
    "high": "",
    "medium": "\n\n---\n*Respuesta aproximada — si no es lo que buscas, intenta reformular.*",
    "low": "\n\n---\n*Respuesta de baja confianza — visita [itla.edu.do](https://www.itla.edu.do)*",
    "fallback": "",
}


def _assistant_msg(content: str) -> dict:
    return {"role": "assistant", "content": content}


def _user_msg(content: str) -> dict:
    return {"role": "user", "content": content}


_INIT_HISTORY: list[dict] = [_assistant_msg(_INITIAL_MSG)]

# ── Quick actions / FAQs ───────────────────────────────────────────────────────
QUICK_ACTIONS = {
    "📚 Oferta Académica":   "¿Cuáles carreras ofrecen en el ITLA?",
    "📝 Inscripción":        "¿Cómo es el proceso de inscripción?",
    "🎓 Educación Continua": "¿Tienen cursos cortos o certificaciones?",
    "🛠️ Soporte":            "Necesito soporte técnico",
    "📞 Contacto":           "¿Cuál es el teléfono y correo del ITLA?",
    "🗺️ Sedes":              "¿En qué provincias tienen sedes?",
}

FAQS = [
    "¿Qué es el ITLA?",
    "¿Cuáles carreras ofrecen?",
    "¿Cómo me inscribo?",
    "¿Dónde están ubicados?",
    "¿Tienen cursos cortos?",
    "¿Cuál es el teléfono del ITLA?",
    "¿Cómo accedo a la plataforma?",
    "¿Hay becas disponibles?",
]

# ── CSS ────────────────────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

.gradio-container, body {
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
    background: #f0f4ff !important;
}

/* ── Hide Gradio chrome ── */
footer,
.gradio-container > footer,
.svelte-byatnx,
button.share-button,
.share-button,
.share-btn-container,
[data-testid="share-button"],
.built-with,
.show-api,
.api-docs-link,
#api-docs,
.gr-screen-recorder,
.record-button,
.overflow-hidden .py-2.px-4.flex.items-center.justify-between { display: none !important; }

/* ── Header ── */
.itla-header {
    background: linear-gradient(135deg, #0b2155 0%, #1d4ed8 60%, #1e40af 100%);
    border-radius: 14px;
    padding: 22px 28px;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 24px rgba(11,33,85,0.18);
}
.itla-logo {
    width: 52px; height: 52px;
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    flex-shrink: 0;
}
.itla-header-text h1 {
    margin: 0;
    font-size: 1.35rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.3px;
}
.itla-header-text p {
    margin: 2px 0 0;
    font-size: 0.82rem;
    color: rgba(255,255,255,0.75);
}
.itla-status {
    margin-left: auto;
    font-size: 0.78rem;
    color: rgba(255,255,255,0.7);
    display: flex; align-items: center; gap: 6px;
}
.itla-status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #4ade80;
    box-shadow: 0 0 8px #4ade80;
    animation: pulse-dot 2s ease-in-out infinite;
}
@keyframes pulse-dot {
    0%,100% { opacity: 1; }
    50%      { opacity: 0.4; }
}

/* ── Chat panel ── */
.chat-panel {
    background: #fff;
    border-radius: 14px;
    box-shadow: 0 2px 12px rgba(11,33,85,0.08);
    overflow: hidden;
    border: 1px solid #e0e7ff;
}

/* Chatbot widget overrides */
.chat-panel .chatbot {
    background: #fff !important;
    border: none !important;
    border-radius: 0 !important;
}

/* User bubbles */
.chat-panel [data-testid="user"] .message,
.chat-panel .message.user,
.chat-panel .user-message {
    background: linear-gradient(135deg, #1d4ed8, #1e40af) !important;
    color: #fff !important;
    border-radius: 16px 16px 4px 16px !important;
    padding: 10px 16px !important;
    box-shadow: 0 2px 8px rgba(29,78,216,0.25) !important;
}

/* Bot bubbles */
.chat-panel [data-testid="bot"] .message,
.chat-panel .message.bot,
.chat-panel .bot-message {
    background: #f8faff !important;
    color: #0f172a !important;
    border-radius: 16px 16px 16px 4px !important;
    border: 1px solid #e0e7ff !important;
    padding: 12px 16px !important;
}

/* ── Input area ── */
.input-row {
    background: #fff;
    border-top: 1px solid #e0e7ff;
    padding: 12px 16px;
    border-radius: 0 0 14px 14px;
}

.input-row textarea {
    border-radius: 10px !important;
    border-color: #c7d2fe !important;
    background: #f8faff !important;
    font-size: 0.95rem !important;
    color: #0f172a !important;
    transition: border-color 0.15s;
}
.input-row textarea:focus {
    border-color: #4f46e5 !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,0.12) !important;
}

/* Send button */
#send-btn {
    background: linear-gradient(135deg, #1d4ed8, #4f46e5) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: opacity 0.15s, transform 0.1s !important;
}
#send-btn:hover  { opacity: 0.9 !important; transform: translateY(-1px) !important; }
#send-btn:active { transform: translateY(0) !important; }

/* Clear button */
#clear-btn {
    background: transparent !important;
    color: #64748b !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 0.82rem !important;
    transition: all 0.15s !important;
}
#clear-btn:hover {
    background: #fee2e2 !important;
    border-color: #fca5a5 !important;
    color: #dc2626 !important;
}

/* ── Sidebar ── */
.sidebar-panel {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.sidebar-section {
    background: #fff;
    border-radius: 12px;
    border: 1px solid #e0e7ff;
    overflow: hidden;
    box-shadow: 0 1px 6px rgba(11,33,85,0.05);
}

.sidebar-title {
    background: #f8faff;
    border-bottom: 1px solid #e0e7ff;
    padding: 10px 14px;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: #4f46e5;
    margin: 0;
}

/* Quick action buttons */
.qa-btn button {
    width: 100% !important;
    background: #fff !important;
    color: #1e3a8a !important;
    border: none !important;
    border-bottom: 1px solid #f1f5f9 !important;
    border-radius: 0 !important;
    text-align: left !important;
    padding: 10px 14px !important;
    font-size: 0.86rem !important;
    font-weight: 500 !important;
    transition: background 0.12s, color 0.12s !important;
    justify-content: flex-start !important;
}
.qa-btn button:hover {
    background: #eff6ff !important;
    color: #1d4ed8 !important;
}
.qa-btn:last-child button { border-bottom: none !important; }

/* FAQ buttons */
.faq-btn button {
    width: 100% !important;
    background: #fff !important;
    color: #374151 !important;
    border: none !important;
    border-bottom: 1px solid #f9fafb !important;
    border-radius: 0 !important;
    text-align: left !important;
    padding: 8px 14px !important;
    font-size: 0.82rem !important;
    transition: background 0.12s !important;
    justify-content: flex-start !important;
}
.faq-btn button:hover {
    background: #f0f4ff !important;
    color: #1d4ed8 !important;
}
.faq-btn:last-child button { border-bottom: none !important; }

/* ── Footer ── */
.itla-footer {
    text-align: center;
    color: #94a3b8;
    font-size: 0.78rem;
    padding: 10px 0 2px;
}
.itla-footer a { color: #6366f1; text-decoration: none; }
.itla-footer a:hover { text-decoration: underline; }

/* ── Dark mode ── */
@media (prefers-color-scheme: dark) {
    .gradio-container, body { background: #0d1117 !important; }

    .chat-panel,
    .sidebar-section { background: #161b27 !important; border-color: #2d3a55 !important; }

    .sidebar-title { background: #1a2236 !important; border-color: #2d3a55 !important; color: #818cf8 !important; }

    .input-row { background: #161b27 !important; border-color: #2d3a55 !important; }
    .input-row textarea { background: #1a2236 !important; color: #e2e8f0 !important; border-color: #2d3a55 !important; }

    .chat-panel .chatbot { background: #161b27 !important; }

    /* Dark bot bubbles */
    .chat-panel [data-testid="bot"] .message,
    .chat-panel .message.bot,
    .chat-panel .bot-message {
        background: #1a2236 !important;
        color: #e2e8f0 !important;
        border-color: #2d3a55 !important;
    }

    .qa-btn button  { background: #161b27 !important; color: #93c5fd !important; border-color: #1e2d47 !important; }
    .qa-btn button:hover { background: #1e2d47 !important; }

    .faq-btn button { background: #161b27 !important; color: #9ca3af !important; border-color: #1e2d47 !important; }
    .faq-btn button:hover { background: #1e2d47 !important; color: #93c5fd !important; }

    #clear-btn { color: #9ca3af !important; border-color: #2d3a55 !important; }
    #clear-btn:hover { background: #3b1212 !important; border-color: #7f1d1d !important; color: #fca5a5 !important; }

    .itla-footer { color: #4b5563 !important; }
}
"""

# ── Chat functions ─────────────────────────────────────────────────────────────

def _stream_response(msg: str, hist: list):
    """Generator: typing indicator → wait for model → real response."""
    msg = msg.strip()
    if not msg:
        yield hist, hist, ""
        return

    # Step 1 — show typing indicator immediately
    pending = list(hist or []) + [
        _user_msg(msg),
        _assistant_msg("✍️ *Escribiendo...*"),
    ]
    yield pending, hist, ""

    # Step 2 — handle cold start (only first run)
    if not _bot_ready.is_set():
        loading = list(hist or []) + [
            _user_msg(msg),
            _assistant_msg(_LOADING_MSG),
        ]
        yield loading, hist, ""
        _bot_ready.wait(timeout=180)

    if _bot is None:
        err = list(hist or []) + [
            _user_msg(msg),
            _assistant_msg("❌ No se pudo iniciar el asistente. Recarga la página."),
        ]
        yield err, err, ""
        return

    # Step 3 — real response
    response, confidence = _bot.respond(msg)
    badge = _CONFIDENCE_BADGES.get(confidence, "")
    new_hist = list(hist or []) + [
        _user_msg(msg),
        _assistant_msg(response + badge),
    ]
    yield new_hist, new_hist, ""


def _quick_reply(question: str, hist: list) -> tuple[list, list]:
    result_hist = hist
    for _, s, _ in _stream_response(question, hist):
        result_hist = s
    return result_hist, result_hist


def _clear() -> tuple[list, list, str]:
    return list(_INIT_HISTORY), list(_INIT_HISTORY), ""


# ── Build UI ───────────────────────────────────────────────────────────────────

def make_demo() -> gr.Blocks:
    # CSS is in launch(), not Blocks() — required by Gradio 6
    with gr.Blocks(title="Asistente ITLA") as demo:
        demo.queue()

        gr.HTML("""
        <div class="itla-header">
            <div class="itla-logo">🎓</div>
            <div class="itla-header-text">
                <h1>Asistente Virtual del ITLA</h1>
                <p>Instituto Tecnológico de Las Américas · IA local y gratuita</p>
            </div>
            <div class="itla-status">
                <div class="itla-status-dot"></div>
                En línea
            </div>
        </div>
        """)

        state = gr.State(list(_INIT_HISTORY))

        with gr.Row(equal_height=False):

            # ── Left: chat ───────────────────────────────────────────────────
            with gr.Column(scale=3):
                with gr.Group(elem_classes="chat-panel"):
                    # No type=, bubble_full_width, show_share_button,
                    # show_copy_button, or avatar_images — not supported here
                    chatbot_ui = gr.Chatbot(
                        value=list(_INIT_HISTORY),
                        height=460,
                        show_label=False,
                    )

                with gr.Row(elem_classes="input-row"):
                    txt_in = gr.Textbox(
                        placeholder="Escribe tu pregunta aquí…",
                        show_label=False,
                        container=False,
                        scale=5,
                        lines=1,
                        max_lines=4,
                    )
                    send_btn = gr.Button("Enviar ➤", scale=1, elem_id="send-btn", min_width=90)

                clear_btn = gr.Button("🗑️ Limpiar conversación", elem_id="clear-btn", size="sm")

            # ── Right: sidebar ───────────────────────────────────────────────
            with gr.Column(scale=1, min_width=210, elem_classes="sidebar-panel"):

                with gr.Group(elem_classes="sidebar-section"):
                    gr.HTML('<p class="sidebar-title">⚡ Acceso rápido</p>')
                    qa_buttons = []
                    for label in QUICK_ACTIONS:
                        b = gr.Button(label, elem_classes="qa-btn", size="sm")
                        qa_buttons.append((label, b))

                with gr.Group(elem_classes="sidebar-section"):
                    gr.HTML('<p class="sidebar-title">💬 Preguntas frecuentes</p>')
                    faq_buttons = []
                    for q in FAQS:
                        b = gr.Button(q, elem_classes="faq-btn", size="sm")
                        faq_buttons.append((q, b))

        gr.HTML(
            '<div class="itla-footer">'
            'ITLA Chatbot · Proyecto académico · '
            '<a href="https://www.itla.edu.do" target="_blank">itla.edu.do</a>'
            '</div>'
        )

        # ── Event wiring ──────────────────────────────────────────────────────

        def _submit(msg, hist):
            for chat_val, st_val, txt_val in _stream_response(msg, hist):
                yield chat_val, st_val, txt_val

        txt_in.submit(_submit,   [txt_in, state], [chatbot_ui, state, txt_in])
        send_btn.click(_submit,  [txt_in, state], [chatbot_ui, state, txt_in])
        clear_btn.click(_clear,  None,            [chatbot_ui, state, txt_in])

        for label, btn in qa_buttons:
            q = QUICK_ACTIONS[label]
            btn.click(
                fn=lambda hist, _q=q: _quick_reply(_q, hist),
                inputs=[state],
                outputs=[chatbot_ui, state],
            )

        for question, btn in faq_buttons:
            btn.click(
                fn=lambda hist, _q=question: _quick_reply(_q, hist),
                inputs=[state],
                outputs=[chatbot_ui, state],
            )

    return demo


if __name__ == "__main__":
    app = make_demo()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
        css=CSS,
    )