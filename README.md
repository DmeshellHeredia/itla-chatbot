Sí, aquí lo tienes en **un solo bloque limpio listo para copiar**:

```markdown
# ITLA Chatbot

> ⚠️ **IMPORTANTE — ESTADO ACTUAL DEL PROYECTO**
>
> 🚧 La **interfaz web (Gradio)** actualmente **NO está funcionando** debido a problemas de compatibilidad y se encuentra **en proceso de corrección**.
>
> ✅ El chatbot **funciona correctamente en modo consola (CLI)**.
>
> 👉 Usa el modo CLI mientras se corrige la interfaz visual.

---

Asistente virtual del Instituto Tecnológico de Las Américas.  
100% local, gratuito, sin APIs de pago.

---

## Arquitectura

```

itla_chatbot/
├── config.py          # Umbrales y parámetros
├── knowledge_base.py  # 13 intents con variantes, keywords y respuestas
├── preprocessor.py    # Normalización de texto (acentos, puntuación, minúsculas)
├── matcher.py         # Keyword scoring + RapidFuzz fuzzy matching
├── semantic.py        # sentence-transformers + FAISS (capa semántica)
├── chatbot.py         # Orquestador del pipeline
├── app.py             # Interfaz web (Gradio) 🚧 (en proceso)
├── cli.py             # Interfaz de línea de comandos ✅
└── test_chatbot.py    # Suite de pruebas

```

---

## Pipeline de matching

```

Input → Preprocesamiento → Keyword scoring
→ Fuzzy matching (RapidFuzz)
→ Semantic search (opcional)
→ Puntuación combinada
→ Umbral de confianza → Respuesta / Fallback

````

---

## Instalación

```bash
pip install -r requirements.txt
````

Modo ligero (sin capa semántica):

```bash
pip install gradio rapidfuzz
```

---

## Uso

### 🖥️ CLI (FUNCIONANDO)

```bash
python cli.py
```

---

### 🌐 Web UI (EN PROCESO 🚧)

```bash
python app.py
# → http://localhost:7860
```

⚠️ Actualmente puede fallar por incompatibilidades de Gradio.

---

### 🧪 Tests

```bash
python test_chatbot.py
```

---

## Umbrales de confianza

| Nivel    | Score | Comportamiento              |
| -------- | ----- | --------------------------- |
| high     | ≥ 65  | Respuesta directa           |
| medium   | ≥ 35  | Respuesta extendida + nota  |
| low      | ≥ 15  | Mejor intento + advertencia |
| fallback | < 15  | Redirección a contacto      |

---

## Agregar nuevos intents

Edita `knowledge_base.py` y agrega un nuevo dict a `INTENTS`.

El engine lo tomará automáticamente.
Borra `.cache/embeddings.pkl` para regenerar embeddings si usas la capa semántica.

---

## Fuente de información

* [https://www.itla.edu.do](https://www.itla.edu.do)

```
```
