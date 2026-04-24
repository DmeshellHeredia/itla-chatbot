"""
Chatbot del ITLA — Interfaz Premium con Gradio
Compatible con la configuración actual de Gradio:
- Historial de mensajes como {"role": "...", "content": "..."}
- Sin type= en gr.Chatbot
- Sin bubble_full_width
- Sin show_api en launch()
- CSS inyectado en launch()
"""

from __future__ import annotations

import threading  # Para cargar el bot en segundo plano sin bloquear la UI

import gradio as gr  # Framework para construir la interfaz web

from chatbot import ChatBot  # Módulo principal con la lógica del chatbot

# URL del perfil de GitHub del autor del proyecto
GITHUB_PROFILE_URL = "https://github.com/DmeshellHeredia"

# ── Carga en segundo plano ────────────────────────────────────────────────────
# El bot se inicializa en un hilo separado para que la interfaz cargue rápido
# mientras el motor semántico (FAISS + sentence-transformers) se prepara
_bot: ChatBot | None = None          # Instancia global del chatbot (None hasta que esté listo)
_bot_ready = threading.Event()        # Evento para sincronizar: se activa cuando el bot está listo


def _load():
    """Inicializa el ChatBot con búsqueda semántica activada y señala que está listo."""
    global _bot
    _bot = ChatBot(use_semantic=True)  # Carga los embeddings y el índice FAISS
    _bot_ready.set()                   # Desbloquea cualquier hilo que esté esperando


# Arranca el hilo de carga en modo daemon (se cierra solo cuando termina el programa)
threading.Thread(target=_load, daemon=True).start()

# ── Constantes de la interfaz ─────────────────────────────────────────────────
# Mensaje de bienvenida que aparece al abrir el chatbot por primera vez
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

# Mensaje que se muestra mientras el motor semántico todavía está cargando
_LOADING_MSG = (
    "⏳ *Iniciando el motor semántico por primera vez...* "
    "Esto puede tardar 20–30 segundos. Solo ocurre en el primer arranque."
)

# Etiquetas de confianza que se añaden al final de cada respuesta según el nivel de certeza
# - "high"    → sin etiqueta (la respuesta es fiable)
# - "medium"  → aviso de respuesta aproximada
# - "low"     → aviso de confianza baja con enlace al sitio oficial
# - "fallback"→ sin etiqueta (el bot usó respuesta de reserva)
_CONFIDENCE_BADGES = {
    "high": "",
    "medium": "\n\n> 💡 *Respuesta aproximada — reformula si necesitas más detalle.*",
    "low": "\n\n> ⚠️ *Confianza baja — visita [itla.edu.do](https://www.itla.edu.do)*",
    "fallback": "",
}


# Funciones auxiliares para crear mensajes con el formato de Gradio
def _am(content: str) -> dict:
    """Crea un mensaje del asistente con el formato esperado por gr.Chatbot."""
    return {"role": "assistant", "content": content}


def _um(content: str) -> dict:
    """Crea un mensaje del usuario con el formato esperado por gr.Chatbot."""
    return {"role": "user", "content": content}


# Historial inicial: solo contiene el mensaje de bienvenida del asistente
_INIT_HISTORY: list[dict] = [_am(_INITIAL_MSG)]

# ── Datos de la barra lateral ──────────────────────────────────────────────────
# Acciones rápidas: botones con un label visible y la pregunta que envían al bot
QUICK_ACTIONS = {
    "📚 Oferta Académica": "¿Cuáles carreras ofrecen en el ITLA?",
    "📝 Inscripción": "¿Cómo es el proceso de inscripción?",
    "🎓 Educación Continua": "¿Tienen cursos cortos o certificaciones?",
    "🛠️ Soporte": "Necesito soporte técnico",
    "📞 Contacto": "¿Cuál es el teléfono y correo del ITLA?",
    "🗺️ Sedes": "¿En qué provincias tienen sedes?",
}

# Preguntas frecuentes que aparecen como botones en la barra lateral
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

# ── JavaScript inyectado en el <head> del HTML ────────────────────────────────
# Este bloque JS se ejecuta antes de que cargue la UI completa para:
# 1. Restaurar el tema guardado en localStorage (evita parpadeo de tema)
# 2. Sincronizar el ícono del botón de tema con el modo activo
# 3. Alternar entre modo oscuro y modo claro al presionar el botón
# 4. Abrir y cerrar el modal "Acerca del proyecto"
_JS_HEAD = """
<script>
(function () {
    // Aplica el tema guardado antes de que se pinte la página para evitar parpadeo
    const saved = localStorage.getItem("itla-theme") || "dark";
    document.documentElement.setAttribute("data-theme", saved);
})();

// Actualiza el ícono del botón según el tema activo (☀️ oscuro → 🌙 claro)
function syncThemeIcon() {
    const icon = document.getElementById("theme-icon");
    if (!icon) return;
    const theme = document.documentElement.getAttribute("data-theme") || "dark";
    icon.textContent = theme === "dark" ? "☀️" : "🌙";
}

// Alterna entre tema oscuro y claro; persiste la elección en localStorage
function toggleTheme() {
    const root = document.documentElement;
    const current = root.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    localStorage.setItem("itla-theme", next);
    syncThemeIcon();
}

// Muestra el modal "Acerca del proyecto"
function openAbout() {
    const modal = document.getElementById("about-overlay");
    if (modal) modal.style.display = "flex";
}

// Oculta el modal "Acerca del proyecto"
function closeAbout() {
    const modal = document.getElementById("about-overlay");
    if (modal) modal.style.display = "none";
}

// Sincroniza el ícono al cargar la página y al terminar de cargar todos los recursos
document.addEventListener("DOMContentLoaded", syncThemeIcon);
window.addEventListener("load", syncThemeIcon);
</script>
"""

# ── Fragmentos HTML estáticos ─────────────────────────────────────────────────
# Modal informativo "Acerca del proyecto" — se muestra al presionar el botón ℹ️ del header.
# Contiene descripción, tecnologías usadas y enlaces externos.
# El overlay cierra si se hace clic fuera de la tarjeta (onclick en el fondo).
_ABOUT_MODAL = f"""
<div id="about-overlay"
     onclick="if(event.target===this)closeAbout()"
     style="display:none;position:fixed;inset:0;z-index:9999;
            background:rgba(0,10,30,.82);backdrop-filter:blur(8px);
            align-items:center;justify-content:center;padding:20px;">
    <div class="about-card">
        <button class="about-x" onclick="closeAbout()">✕</button>
        <div class="about-hdr">
            <div class="about-icon">🎓</div>
            <div>
                <div class="about-name">ITLA Chatbot</div>
                <div class="about-tagline">Asistente Virtual Inteligente</div>
            </div>
        </div>
        <p class="about-desc">
            Asistente virtual del Instituto Tecnológico de Las Américas, construido como
            proyecto académico de NLP e IA local. Funciona completamente en tu máquina,
            sin APIs externas ni costos de ningún tipo.
        </p>
        <div class="about-grid">
            <div class="about-chip">
                <div class="chip-lbl">Motor NLP</div>
                <div class="chip-val">RapidFuzz + Fuzzy Matching</div>
            </div>
            <div class="about-chip">
                <div class="chip-lbl">Búsqueda Semántica</div>
                <div class="chip-val">FAISS + sentence-transformers</div>
            </div>
            <div class="about-chip">
                <div class="chip-lbl">Interfaz</div>
                <div class="chip-val">Gradio + Python</div>
            </div>
            <div class="about-chip about-chip-green">
                <div class="chip-lbl" style="color:#22c55e;">Privacidad</div>
                <div class="chip-val">100% local · Sin APIs de pago</div>
            </div>
        </div>
        <div class="about-actions">
            <a href="{GITHUB_PROFILE_URL}" target="_blank" class="about-btn about-ghost">
                ⬡&nbsp; Ver en GitHub
            </a>
            <a href="https://www.itla.edu.do" target="_blank" class="about-btn about-primary">
                🌐&nbsp; itla.edu.do
            </a>
        </div>
    </div>
</div>
"""

# Logo y nombre del ITLA que aparece en la parte superior de la barra lateral
_SIDEBAR_BRAND = """
<div class="sb-brand">
    <div class="sb-logo">🎓</div>
    <div>
        <div class="sb-title">ITLA</div>
        <div class="sb-sub">Asistente Virtual</div>
    </div>
</div>
"""

# Encabezado principal de la sección de chat:
# muestra nombre, subtítulo, indicador de estado en línea y botones de tema/info
_HEADER_HTML = """
<div class="main-header">
    <div class="hdr-left">
        <div class="hdr-icon">🤖</div>
        <div>
            <h1 class="hdr-title">Asistente Virtual del ITLA</h1>
            <p class="hdr-sub">Instituto Tecnológico de Las Américas · IA local y gratuita</p>
        </div>
    </div>
    <div class="hdr-right">
        <div class="hdr-status">
            <span class="status-dot"></span>En línea
        </div>
        <button class="hdr-btn" onclick="toggleTheme()" title="Cambiar tema">
            <span id="theme-icon">☀️</span>
        </button>
        <button class="hdr-btn" onclick="openAbout()" title="Acerca del proyecto">ℹ️</button>
    </div>
</div>
"""

# ── Estilos CSS ────────────────────────────────────────────────────────────────
# Toda la hoja de estilos de la aplicación. Está organizada en secciones:
# 1. Variables de diseño (colores, sombras, tipografía)
# 2. Tema claro (sobreescribe las variables del tema oscuro)
# 3. Reset y base
# 4. Contenedor Gradio (ancho completo sin romper el layout)
# 5. Ocultar elementos de la UI de Gradio que no queremos mostrar
# 6. Estructura principal (shell, sidebar, área principal)
# 7. Componentes: encabezado, chat, input, modal, botones
# 8. Parches de legibilidad (texto visible en ambos temas)
# 9. Diseño responsivo (breakpoints para tablets y móviles)
CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* ── Variables del tema oscuro (valores por defecto) ── */
:root {
    --bg: #071224;
    --surface: #0b1628;
    --surface-2: #0f1e35;
    --surface-3: #122540;
    --border: #1a2e4f;
    --border-2: #27426d;
    --accent: #2563eb;
    --accent-2: #3b82f6;
    --accent-3: #4338ca;
    --text: #dbe8fb;
    --text-soft: #8aa0c5;
    --text-dim: #54719d;
    --success: #22c55e;
    --danger: #ef4444;
    --shadow: 0 10px 28px rgba(0, 0, 0, .28);
    --radius: 16px;
    --font: 'Outfit', system-ui, sans-serif;
}

/* ── Variables del tema claro (sobreescribe las de arriba) ── */
html[data-theme="light"] {
    --bg: #eef4ff;
    --surface: #ffffff;
    --surface-2: #f6f9ff;
    --surface-3: #edf3ff;
    --border: #d7e2f7;
    --border-2: #b9cbee;
    --accent: #2563eb;
    --accent-2: #3b82f6;
    --accent-3: #4338ca;
    --text: #122033;
    --text-soft: #506b92;
    --text-dim: #8397b3;
    --shadow: 0 10px 28px rgba(37, 99, 235, .08);
}

/* ── Reset de box-sizing para todos los elementos ── */
*,
*::before,
*::after {
    box-sizing: border-box;
}

/* ── Base: fondo y tipografía globales ── */
html, body {
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh;
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
}

/* ── Contenedor Gradio: ancho completo sin romper el layout ── */
.gradio-container,
.gradio-container .main,
.gradio-container .contain,
.contain,
.main {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    background: var(--bg) !important;
}

/* ── Ocultar elementos nativos de Gradio que no forman parte del diseño ── */
footer,
.gradio-container > footer,
button.share-button,
.share-button,
.share-btn-container,
[data-testid="share-button"],
.built-with,
.show-api,
.api-docs-link,
#api-docs,
.gradio-api-info,
.gradio-footer,
a[href*="gradio.app"],
a[href*="huggingface"],
button[aria-label*="Share"],
button[title*="Share"],
button[title*="API"],
button[aria-label*="API"],
.svelte-byatnx,
.gr-screen-recorder,
.record-button {
    display: none !important;
}

/* ── Ocultar botones de acción sobre mensajes del chat (copiar, compartir, editar) ── */
[data-testid="chatbot"] button[aria-label],
[data-testid="chatbot"] button[title],
.message-actions,
[class*="message-action"],
[class*="copy-btn"],
[class*="share-btn"],
[class*="edit-btn"] {
    display: none !important;
}

/* ── Shell principal: layout de dos columnas (sidebar + contenido) ── */
#app-shell {
    display: flex !important;
    align-items: stretch !important;
    gap: 0 !important;
    min-height: 100vh !important;
    flex-wrap: nowrap !important;
}

/* ── Barra lateral: ancho fijo, no crece ni se encoge ── */
#sidebar {
    width: 285px !important;
    min-width: 285px !important;
    max-width: 285px !important;
    flex: 0 0 285px !important;
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    padding: 0 !important;
}

#sidebar > div {
    height: 100%;
}

/* Columna flexible dentro del sidebar para empujar el footer hacia abajo */
.sidebar-stack {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    gap: 0;
}

/* ── Marca/logo en la parte superior del sidebar ── */
.sb-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 22px 18px 18px;
    border-bottom: 1px solid var(--border);
}

.sb-logo {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, var(--accent), var(--accent-3));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 21px;
    box-shadow: 0 6px 16px rgba(37,99,235,.22);
}

.sb-title {
    font-size: 1rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -.2px;
}

.sb-sub {
    margin-top: 2px;
    font-size: .72rem;
    color: var(--text-dim);
}

/* ── Encabezados de sección dentro del sidebar ── */
.sb-section-title {
    padding: 16px 18px 8px;
    font-size: .7rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--accent-2);
    border-top: 1px solid var(--border);
    background: var(--surface-2);
}

/* Espaciador flexible: empuja el footer al fondo del sidebar */
.sb-spacer {
    flex: 1 1 auto;
}

/* ── Footer del sidebar con enlace al sitio oficial y nota de copyright ── */
.sb-footer {
    margin-top: auto;
    padding: 16px 18px 18px;
    border-top: 1px solid var(--border);
}

.sb-footer-link {
    display: block;
    text-decoration: none;
    color: var(--accent-2);
    font-weight: 700;
    font-size: .9rem;
    text-align: center;
    margin-bottom: 6px;
}

.sb-footer-link:hover {
    text-decoration: underline;
}

.sb-footer-copy {
    text-align: center;
    font-size: .72rem;
    color: var(--text-dim);
}

/* ── Botones de acciones rápidas y preguntas frecuentes en el sidebar ── */
/* Alineados a la izquierda, sin borde propio, con animación de deslizamiento al hacer hover */
.qa-sb-btn button,
.faq-sb-btn button {
    width: 100% !important;
    justify-content: flex-start !important;
    text-align: left !important;
    border: none !important;
    border-bottom: 1px solid var(--border) !important;
    border-radius: 0 !important;
    background: transparent !important;
    color: var(--text-soft) !important;
    padding: 10px 18px !important;
    font-family: var(--font) !important;
    transition: background .16s ease, color .16s ease, padding-left .16s ease !important;
}

/* Acciones rápidas: texto más grande y en negrita */
.qa-sb-btn button {
    font-size: .88rem !important;
    font-weight: 600 !important;
}

/* Preguntas frecuentes: texto más pequeño y peso normal */
.faq-sb-btn button {
    font-size: .82rem !important;
    font-weight: 500 !important;
}

/* Efecto hover: fondo destacado y ligero desplazamiento del texto */
.qa-sb-btn button:hover,
.faq-sb-btn button:hover {
    background: var(--surface-3) !important;
    color: var(--text) !important;
    padding-left: 22px !important;
}

/* ── Área de contenido principal (columna derecha) ── */
#main-area {
    flex: 1 1 auto !important;
    min-width: 0 !important;
    padding: 18px 22px 22px !important;
    background: var(--bg) !important;
}

#main-area > div {
    display: flex;
    flex-direction: column;
    gap: 14px;
}

/* ── Encabezado principal con gradiente azul ── */
.main-header {
    display: flex;
    align-items: center;
    gap: 14px;
    background: linear-gradient(135deg, #0b2155 0%, #1d4ed8 55%, #2563eb 100%);
    border-radius: 18px;
    padding: 18px 22px;
    box-shadow: 0 10px 30px rgba(11,33,85,.28);
}

.hdr-left {
    display: flex;
    align-items: center;
    gap: 14px;
    flex: 1;
    min-width: 0;
}

.hdr-right {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
}

/* Ícono del robot en el encabezado */
.hdr-icon {
    width: 46px;
    height: 46px;
    border-radius: 12px;
    background: rgba(255,255,255,.14);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
}

.hdr-title {
    margin: 0;
    color: #fff;
    font-size: 1.2rem;
    font-weight: 800;
    letter-spacing: -.3px;
}

.hdr-sub {
    margin: 3px 0 0;
    color: rgba(255,255,255,.76);
    font-size: .8rem;
}

/* Indicador de estado "En línea" con píldora semitransparente */
.hdr-status {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: .8rem;
    color: #fff;
    background: rgba(255,255,255,.12);
    border: 1px solid rgba(255,255,255,.16);
    border-radius: 999px;
    padding: 6px 12px;
}

/* Punto verde animado que indica estado activo */
.status-dot {
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: var(--success);
    box-shadow: 0 0 8px var(--success);
}

/* Botones del encabezado (tema e info) */
.hdr-btn {
    width: 36px;
    height: 36px;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,.16) !important;
    background: rgba(255,255,255,.12) !important;
    color: #fff !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    cursor: pointer !important;
    font-size: 15px !important;
    transition: background .16s ease !important;
}

.hdr-btn:hover {
    background: rgba(255,255,255,.22) !important;
}

/* ── Envoltorio del chat: columna con espacio entre panel e input ── */
#chat-wrap {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

/* ── Panel del chat: tarjeta con borde y sombra ── */
.chat-panel {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 18px !important;
    box-shadow: var(--shadow) !important;
    overflow: hidden !important;
}

.chat-panel .chatbot {
    background: var(--surface) !important;
    border: none !important;
}

/* ── Burbujas de mensajes del chatbot ── */
/* Burbuja del asistente: fondo oscuro secundario con borde */
.chat-panel [data-testid="bot"] [class*="message"],
.chat-panel .message.bot,
.chat-panel .bot {
    background: var(--surface-2) !important;
    border: 1px solid var(--border-2) !important;
    color: var(--text) !important;
    border-radius: 16px 16px 16px 6px !important;
    box-shadow: none !important;
}

/* Burbuja del usuario: gradiente azul con sombra sutil */
.chat-panel [data-testid="user"] [class*="message"],
.chat-panel .message.user,
.chat-panel .user {
    background: linear-gradient(135deg, var(--accent), var(--accent-3)) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 16px 16px 6px 16px !important;
    box-shadow: 0 6px 18px rgba(37,99,235,.25) !important;
}

/* ── Correcciones de legibilidad en modo claro para el panel del chat ── */
html[data-theme="light"] .chat-panel {
    background: #ffffff !important;
    border-color: #d3dff5 !important;
}

html[data-theme="light"] .chat-panel .chatbot {
    background: #ffffff !important;
}

html[data-theme="light"] .chat-panel [data-testid="bot"] [class*="message"],
html[data-theme="light"] .chat-panel .message.bot,
html[data-theme="light"] .chat-panel .bot {
    background: #f6f9ff !important;
    border: 1px solid #c8d7f0 !important;
    color: #16253a !important;
}

html[data-theme="light"] .chat-panel [data-testid="user"] [class*="message"],
html[data-theme="light"] .chat-panel .message.user,
html[data-theme="light"] .chat-panel .user {
    color: #ffffff !important;
}

/* Hereda el color del contenedor en lugar de forzar uno propio */
html[data-theme="light"] .chat-panel p,
html[data-theme="light"] .chat-panel li,
html[data-theme="light"] .chat-panel span,
html[data-theme="light"] .chat-panel div {
    color: inherit !important;
}

/* ── Fila de entrada de texto ── */
.input-row {
    display: flex !important;
    gap: 10px !important;
    align-items: flex-end !important;
}

/* Estilo compartido para textarea e input de texto */
.input-row textarea,
.input-row input,
textarea {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-family: var(--font) !important;
    font-size: .95rem !important;
}

/* Resaltado azul al enfocar el campo de texto */
.input-row textarea:focus,
textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,.14) !important;
}

/* Ajuste de colores del textarea en modo claro */
html[data-theme="light"] .input-row textarea,
html[data-theme="light"] textarea {
    background: #ffffff !important;
    color: #16253a !important;
    border-color: #d0def7 !important;
}

/* Botón "Enviar": gradiente azul con efecto de elevación al hacer hover */
#send-btn {
    background: linear-gradient(135deg, var(--accent), var(--accent-3)) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-family: var(--font) !important;
    box-shadow: 0 6px 18px rgba(37,99,235,.22) !important;
    transition: transform .16s ease, opacity .16s ease !important;
}

#send-btn:hover {
    transform: translateY(-1px) !important;
    opacity: .92 !important;
}

/* Botón "Limpiar conversación": sutil, se vuelve rojo al hacer hover */
#clear-btn {
    width: fit-content !important;
    background: transparent !important;
    color: var(--text-dim) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-size: .82rem !important;
    font-family: var(--font) !important;
}

#clear-btn:hover {
    background: rgba(239,68,68,.1) !important;
    color: var(--danger) !important;
    border-color: var(--danger) !important;
}

/* ── Modal "Acerca del proyecto" ── */
.about-card {
    width: 100%;
    max-width: 520px;
    background: var(--surface);
    border: 1px solid var(--border-2);
    border-radius: 22px;
    padding: 30px;
    position: relative;
    box-shadow: 0 30px 70px rgba(0,0,0,.45);
    color: var(--text);
}

/* Botón de cierre (X) posicionado en la esquina superior derecha */
.about-x {
    position: absolute;
    top: 14px;
    right: 14px;
    width: 32px;
    height: 32px;
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    background: var(--surface-2) !important;
    color: var(--text-soft) !important;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer !important;
}

/* Encabezado del modal: ícono + nombre del proyecto */
.about-hdr {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 16px;
}

.about-icon {
    width: 52px;
    height: 52px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--accent), var(--accent-3));
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}

.about-name {
    font-size: 1.16rem;
    font-weight: 800;
    color: var(--text);
}

.about-tagline {
    margin-top: 2px;
    font-size: .8rem;
    color: var(--text-soft);
}

.about-desc {
    color: var(--text-soft);
    font-size: .9rem;
    line-height: 1.65;
    margin-bottom: 18px;
}

/* Cuadrícula de chips con información técnica del proyecto */
.about-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 18px;
}

.about-chip {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 12px;
}

/* Chip especial con acento verde para la sección de privacidad */
.about-chip-green {
    border-color: rgba(34,197,94,.25);
    background: rgba(34,197,94,.06);
}

.chip-lbl {
    font-size: .68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: var(--accent-2);
    margin-bottom: 4px;
}

.chip-val {
    font-size: .86rem;
    color: var(--text);
    font-weight: 500;
}

/* Fila de botones de acción al pie del modal */
.about-actions {
    display: flex;
    gap: 10px;
}

.about-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border-radius: 12px;
    padding: 11px;
    text-decoration: none;
    font-size: .86rem;
    font-weight: 700;
    transition: transform .16s ease, opacity .16s ease;
}

/* Botón fantasma: fondo translúcido con borde */
.about-ghost {
    background: var(--surface-2);
    color: var(--text-soft);
    border: 1px solid var(--border);
}

/* Botón principal: gradiente azul sin borde */
.about-primary {
    background: linear-gradient(135deg, var(--accent), var(--accent-3));
    color: #ffffff;
    border: none;
}

/* Efecto hover compartido: elevación sutil */
.about-btn:hover {
    transform: translateY(-1px);
    opacity: .94;
}

/* ── Diseño responsivo ── */
/* Tablet: sidebar más angosto */
@media (max-width: 980px) {
    #sidebar {
        width: 240px !important;
        min-width: 240px !important;
        max-width: 240px !important;
        flex-basis: 240px !important;
    }
}

/* Móvil: sidebar oculto, padding reducido, layouts en columna */
@media (max-width: 760px) {
    #sidebar {
        display: none !important;
    }

    #main-area {
        padding: 14px !important;
    }

    .about-grid {
        grid-template-columns: 1fr;
    }

    .about-actions {
        flex-direction: column;
    }
}
/* ===== CORRECCIONES FINALES DE UI ===== */
/* Garantizan que el layout ocupe toda la pantalla verticalmente
   y que los elementos principales no generen scroll horizontal */

html,
body,
.gradio-container {
    min-height: 100vh !important;
    overflow-x: hidden !important;
}

#app-shell {
    min-height: 100vh !important;
    display: flex !important;
    align-items: stretch !important;
    overflow: visible !important;
}

#sidebar {
    min-height: 100vh !important;
    overflow-y: auto !important;    /* scroll vertical si el contenido es muy largo */
}

#main-area {
    min-height: 100vh !important;
    overflow: visible !important;
}

#main-area > div {
    display: flex !important;
    flex-direction: column !important;
    gap: 14px !important;
}

/* Panel del chat con altura mínima y máxima fija para evitar colapso */
.chat-panel {
    display: block !important;
    min-height: 520px !important;
    max-height: 620px !important;
    overflow: hidden !important;
}

#chatbot-main {
    min-height: 520px !important;
}

/* ── Ocultar botones de acción nativos de Gradio dentro del chatbot ── */
#chatbot-main button[title],
#chatbot-main button[aria-label],
#chatbot-main [class*="copy"],
#chatbot-main [class*="share"],
#chatbot-main [class*="delete"],
#chatbot-main [class*="trash"],
#chatbot-main [class*="message-action"],
#chatbot-main [class*="message-button"] {
    display: none !important;
}

/* ── Burbujas del bot: sin doble borde ni sombra extra ── */
#chatbot-main [data-testid="bot"] [class*="message"],
#chatbot-main .bot,
#chatbot-main .message.bot {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: var(--surface-2) !important;
}

/* ── Legibilidad del texto dentro del chat ── */
#chatbot-main p,
#chatbot-main li,
#chatbot-main span,
#chatbot-main div,
#chatbot-main strong,
#chatbot-main b {
    color: var(--text) !important;
}

/* Negritas más pronunciadas para mejorar la jerarquía visual */
#chatbot-main strong,
#chatbot-main b {
    font-weight: 800 !important;
}

/* Marcadores de lista en color acento para mejor distinción visual */
#chatbot-main li::marker {
    color: var(--accent-2) !important;
}

/* ── Legibilidad en modo claro ── */
html[data-theme="light"] #chatbot-main [data-testid="bot"] [class*="message"],
html[data-theme="light"] #chatbot-main .bot,
html[data-theme="light"] #chatbot-main .message.bot {
    background: #ffffff !important;
    color: #111827 !important;
}

html[data-theme="light"] #chatbot-main p,
html[data-theme="light"] #chatbot-main li,
html[data-theme="light"] #chatbot-main span,
html[data-theme="light"] #chatbot-main div,
html[data-theme="light"] #chatbot-main strong,
html[data-theme="light"] #chatbot-main b {
    color: #111827 !important;
}

/* Encabezado de sección del sidebar en modo claro: fondo oscuro para contraste */
html[data-theme="light"] .sb-section-title {
    background: #0f1e35 !important;
    color: #60a5fa !important;
}

/* Botones del sidebar en modo claro: texto oscuro sobre fondo casi blanco */
html[data-theme="light"] .qa-sb-btn button,
html[data-theme="light"] .faq-sb-btn button {
    background: #f8fbff !important;
    color: #111827 !important;
}

/* Altura mínima del botón Enviar para facilitar el toque en móviles */
#send-btn {
    min-height: 44px !important;
    max-height: 52px !important;
}
/* ===== PARCHE DE LEGIBILIDAD ===== */
/* Asegura que todo el texto dentro del chatbot sea legible en ambos temas.
   Las sombras de texto pueden reducir el contraste, así que se eliminan. */

#chatbot-main,
#chatbot-main * {
    text-shadow: none !important;
}

/* ── Burbuja del bot en tema oscuro: fondo y color base ── */
#chatbot-main [data-testid="bot"] [class*="message"],
#chatbot-main .message.bot,
#chatbot-main .bot {
    background: var(--surface-2) !important;
    color: var(--text) !important;
}

/* ── Forzar color legible en todos los elementos de texto dentro del chat ── */
#chatbot-main p,
#chatbot-main li,
#chatbot-main span,
#chatbot-main div,
#chatbot-main strong,
#chatbot-main b,
#chatbot-main em,
#chatbot-main i,
#chatbot-main blockquote,
#chatbot-main a {
    color: var(--text) !important;
    opacity: 1 !important;
}

/* Los enlaces dentro del chat se muestran en azul acento con subrayado */
#chatbot-main a {
    text-decoration: underline !important;
    color: var(--accent-2) !important;
}

/* Citas en bloque: borde izquierdo azul y fondo ligeramente tintado */
#chatbot-main blockquote {
    border-left: 4px solid var(--accent-2) !important;
    background: rgba(59, 130, 246, 0.08) !important;
    padding: 8px 12px !important;
    margin: 12px 0 0 !important;
    border-radius: 8px !important;
}

/* ── Correcciones de legibilidad en modo claro para el bot ── */
html[data-theme="light"] #chatbot-main [data-testid="bot"] [class*="message"],
html[data-theme="light"] #chatbot-main .message.bot,
html[data-theme="light"] #chatbot-main .bot {
    background: #f8fbff !important;
    color: #111827 !important;
}

html[data-theme="light"] #chatbot-main p,
html[data-theme="light"] #chatbot-main li,
html[data-theme="light"] #chatbot-main span,
html[data-theme="light"] #chatbot-main div,
html[data-theme="light"] #chatbot-main strong,
html[data-theme="light"] #chatbot-main b,
html[data-theme="light"] #chatbot-main em,
html[data-theme="light"] #chatbot-main i,
html[data-theme="light"] #chatbot-main blockquote {
    color: #111827 !important;
    opacity: 1 !important;
}

/* Enlace en modo claro: azul más intenso para contraste sobre fondo blanco */
html[data-theme="light"] #chatbot-main a {
    color: #1d4ed8 !important;
    opacity: 1 !important;
}

/* Blockquote en modo claro: fondo azul muy suave y borde sólido */
html[data-theme="light"] #chatbot-main blockquote {
    background: #eaf2ff !important;
    border-left-color: #2563eb !important;
}

/* Evita que las notas al pie en cursiva queden invisibles sobre fondo claro */
html[data-theme="light"] #chatbot-main em,
html[data-theme="light"] #chatbot-main i {
    color: #374151 !important;
}
"""

# ── Funciones del chat ─────────────────────────────────────────────────────────
def _stream_response(msg: str, hist: list):
    """
    Genera respuestas de forma progresiva (streaming simulado).

    Flujo:
    1. Muestra un indicador "Escribiendo..." inmediatamente.
    2. Espera a que el bot esté listo si todavía está cargando.
    3. Llama a _bot.respond() para obtener la respuesta real.
    4. Añade la etiqueta de confianza correspondiente y actualiza el historial.

    Yields:
        Tuplas (chat_value, state_value, input_value) que Gradio usa para
        actualizar el chatbot, el estado y limpiar el campo de texto.
    """
    msg = msg.strip()
    # Si el mensaje está vacío, no hacer nada y devolver el estado actual
    if not msg:
        yield hist, hist, ""
        return

    # Paso 1: mostrar indicador de escritura antes de consultar al bot
    yield list(hist) + [_um(msg), _am("✍️ *Escribiendo...*")], hist, ""

    # Paso 2: esperar si el motor semántico aún no ha terminado de cargar
    if not _bot_ready.is_set():
        yield list(hist) + [_um(msg), _am(_LOADING_MSG)], hist, ""
        _bot_ready.wait(timeout=180)  # Esperar hasta 3 minutos máximo

    # Paso 3: verificar que el bot se inicializó correctamente
    if _bot is None:
        err = list(hist) + [_um(msg), _am("❌ No se pudo iniciar el asistente. Recarga la página.")]
        yield err, err, ""
        return

    # Paso 4: obtener respuesta + nivel de confianza y armar el historial final
    response, confidence = _bot.respond(msg)
    badge = _CONFIDENCE_BADGES.get(confidence, "")  # Etiqueta vacía si la confianza es alta
    new_hist = list(hist) + [_um(msg), _am(response + badge)]
    yield new_hist, new_hist, ""


def _quick_reply(question: str, hist: list) -> tuple[list, list]:
    """
    Envía una pregunta predefinida (desde el sidebar) y retorna el historial actualizado.
    Consume el generador de _stream_response hasta la última iteración.
    """
    result = hist
    for _, s, _ in _stream_response(question, hist):
        result = s  # Toma solo el estado final del historial
    return result, result


def _clear(hist: list) -> tuple[list, list, str]:
    """
    Limpia el historial del chat y reinicia la conversación al mensaje de bienvenida.
    No hace nada si el usuario aún no ha enviado ningún mensaje.
    """
    # Si no hay mensajes del usuario, no hay nada que limpiar
    if not any(m.get("role") == "user" for m in (hist or [])):
        return hist, hist, ""
    # Restaurar el historial inicial con solo el mensaje de bienvenida
    return list(_INIT_HISTORY), list(_INIT_HISTORY), ""


# ── Construcción de la interfaz de usuario ─────────────────────────────────────
def make_demo() -> gr.Blocks:
    """
    Construye y devuelve el objeto gr.Blocks con toda la interfaz del chatbot.

    Estructura del layout:
    ┌─────────────┬───────────────────────────────────────┐
    │   Sidebar   │            Área principal              │
    │  (285px)    │  ┌─────────────────────────────────┐  │
    │  - Marca    │  │         Encabezado               │  │
    │  - Acciones │  ├─────────────────────────────────┤  │
    │    rápidas  │  │       Panel del chatbot          │  │
    │  - FAQs     │  ├─────────────────────────────────┤  │
    │  - Footer   │  │   Fila de entrada + Enviar       │  │
    │             │  │   Botón Limpiar conversación     │  │
    └─────────────┴──┴─────────────────────────────────┴──┘
    """
    with gr.Blocks(title="ITLA · Asistente Virtual", head=_JS_HEAD) as demo:
        demo.queue()  # Habilitar cola para manejar múltiples usuarios simultáneos

        # Modal de información (invisible por defecto, se activa con JS)
        gr.HTML(_ABOUT_MODAL)

        # Estado global: mantiene el historial de mensajes entre interacciones
        state = gr.State(list(_INIT_HISTORY))

        with gr.Row(elem_id="app-shell", equal_height=False):

            # ── Columna izquierda: sidebar de navegación ──
            with gr.Column(elem_id="sidebar", scale=0):
                with gr.Group(elem_classes="sidebar-stack"):
                    gr.HTML(_SIDEBAR_BRAND)  # Logo + nombre

                    # Sección de acciones rápidas
                    gr.HTML('<div class="sb-section-title">⚡ Acceso Rápido</div>')
                    qa_buttons: list[tuple[str, gr.Button]] = []
                    for label in QUICK_ACTIONS:
                        b = gr.Button(label, elem_classes="qa-sb-btn", size="sm")
                        qa_buttons.append((label, b))  # Guardar referencia para conectar eventos

                    # Sección de preguntas frecuentes
                    gr.HTML('<div class="sb-section-title">💬 Preguntas Frecuentes</div>')
                    faq_buttons: list[tuple[str, gr.Button]] = []
                    for q in FAQS:
                        b = gr.Button(q, elem_classes="faq-sb-btn", size="sm")
                        faq_buttons.append((q, b))  # Guardar referencia para conectar eventos

                    gr.HTML('<div class="sb-spacer"></div>')  # Empuja el footer hacia abajo

                    # Footer del sidebar con enlace al sitio oficial
                    gr.HTML(
                        """
                        <div class="sb-footer">
                            <a href="https://www.itla.edu.do" target="_blank" class="sb-footer-link">🌐 itla.edu.do</a>
                            <div class="sb-footer-copy">ITLA Chatbot · Proyecto académico</div>
                        </div>
                        """
                    )

            # ── Columna derecha: área principal con chat ──
            with gr.Column(elem_id="main-area", scale=1):
                gr.HTML(_HEADER_HTML)  # Encabezado con título y botones

                # Panel del chat con el componente Chatbot de Gradio
                with gr.Group(elem_classes="chat-panel"):
                    chatbot_ui = gr.Chatbot(
                        value=list(_INIT_HISTORY),  # Muestra el mensaje de bienvenida al cargar
                        height=520,
                        show_label=False,
                        elem_id="chatbot-main",
                    )

                # Fila de entrada: campo de texto + botón Enviar
                with gr.Row(elem_classes="input-row"):
                    txt_in = gr.Textbox(
                        placeholder="Escribe tu pregunta aquí…",
                        show_label=False,
                        container=False,
                        scale=5,       # Ocupa 5/6 del espacio disponible
                        lines=1,
                        max_lines=4,   # Expande hasta 4 líneas antes de hacer scroll
                    )
                    send_btn = gr.Button("Enviar ➤", elem_id="send-btn", scale=1, min_width=120)

                # Botón para resetear la conversación
                clear_btn = gr.Button("🗑️ Limpiar conversación", elem_id="clear-btn", size="sm")

        # ── Función interna que reenvía al generador principal ──
        # Necesaria porque Gradio requiere que los generadores estén definidos dentro
        # del bloque gr.Blocks para que los eventos funcionen correctamente
        def _submit(msg, hist):
            for cv, sv, tv in _stream_response(msg, hist):
                yield cv, sv, tv

        # ── Conectar eventos de la fila de entrada ──
        # Enter en el textarea y clic en Enviar ejecutan la misma función
        txt_in.submit(_submit, [txt_in, state], [chatbot_ui, state, txt_in])
        send_btn.click(_submit, [txt_in, state], [chatbot_ui, state, txt_in])

        # El botón Limpiar reinicia el historial sin necesidad de recargar la página
        clear_btn.click(_clear, [state], [chatbot_ui, state, txt_in])

        # ── Conectar botones de acciones rápidas del sidebar ──
        # Cada botón envía la pregunta correspondiente de QUICK_ACTIONS
        # El argumento _q=q captura el valor en el momento del bucle (cierre de variable)
        for label, btn in qa_buttons:
            q = QUICK_ACTIONS[label]
            btn.click(fn=lambda h, _q=q: _quick_reply(_q, h), inputs=[state], outputs=[chatbot_ui, state])

        # ── Conectar botones de preguntas frecuentes del sidebar ──
        for question, btn in faq_buttons:
            btn.click(fn=lambda h, _q=question: _quick_reply(_q, h), inputs=[state], outputs=[chatbot_ui, state])

    return demo


# ── Punto de entrada ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = make_demo()
    app.launch(
        server_name="0.0.0.0",   # Escuchar en todas las interfaces de red
        server_port=7860,         # Puerto por defecto de Gradio
        share=False,              # No crear túnel público en Hugging Face
        inbrowser=True,           # Abrir el navegador automáticamente al iniciar
        css=CSS,                  # Inyectar los estilos personalizados
    )
