# 🎓 ITLA Chatbot

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange)
![AI](https://img.shields.io/badge/NLP-Hybrid-green)
![Status](https://img.shields.io/badge/status-active-success)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 🚀 Descripción

Asistente virtual del **Instituto Tecnológico de Las Américas (ITLA)** construido completamente en Python.

Este chatbot utiliza un enfoque híbrido de procesamiento de lenguaje natural (NLP) combinando:

- Matching por keywords
- Fuzzy matching (RapidFuzz)
- Búsqueda semántica (Sentence Transformers + FAISS)

💡 **100% local, sin APIs externas, sin costos.**

---

## ✨ Demo

### 🌐 Interfaz Web
```bash
python app.py
````

### 🖥️ Consola

```bash
python cli.py
```

---

## 🧠 Características principales

* 🔎 NLP híbrido (keyword + fuzzy + semantic)
* ⚡ Respuestas rápidas offline
* 🎯 Sistema de confianza (high / medium / low / fallback)
* 💬 UI moderna con Gradio
* 🧪 Tests automatizados (28/28 ✅)
* 📚 Base de conocimiento escalable
* 🌙 Dark / Light mode

---

## 📊 Métricas del proyecto

* ✅ **13 intents**
* ✅ **180+ variantes de preguntas**
* ✅ **28 casos de prueba**
* ✅ **100% tests passing**
* ✅ Manejo de errores y fallback inteligente

---

## 🏗️ Arquitectura

```text
itla_chatbot/
├── config.py
├── knowledge_base.py
├── preprocessor.py
├── matcher.py
├── semantic.py
├── chatbot.py
├── app.py
├── cli.py
└── test_chatbot.py
```

---

## ⚙️ Pipeline NLP

```text
Input
 ↓
Preprocessing
 ↓
Keyword Matching
 ↓
Fuzzy Matching
 ↓
Semantic Search (optional)
 ↓
Score fusion
 ↓
Confidence evaluation
 ↓
Response / Fallback
```

---

## 📦 Instalación

```bash
pip install -r requirements.txt
```

Modo ligero:

```bash
pip install gradio rapidfuzz
```

---

## ▶️ Uso

### Web UI (recomendado)

```bash
python app.py
```

### CLI

```bash
python cli.py
```

### Tests

```bash
python test_chatbot.py
```

---

## 📈 Sistema de confianza

| Nivel    | Score | Acción                  |
| -------- | ----: | ----------------------- |
| high     |  ≥ 65 | Respuesta directa       |
| medium   |  ≥ 35 | Respuesta contextual    |
| low      |  ≥ 15 | Sugerencia aproximada   |
| fallback |  < 15 | No entendió la pregunta |

---

## ➕ Extensión del sistema

Agregar nuevos intents:

1. Editar `knowledge_base.py`
2. Añadir nuevo objeto en `INTENTS`
3. (Opcional) regenerar embeddings:

```bash
rm -rf .cache
```

---

## 📌 Ejemplos de preguntas

* ¿Qué es el ITLA?
* ¿Cómo me inscribo?
* ¿Qué carreras ofrecen?
* ¿Dónde están ubicados?
* ¿Qué es Moodle?
* ¿Tienen cursos cortos?
* ¿Hay becas disponibles?

---

## 🌍 Fuente

* [https://www.itla.edu.do](https://www.itla.edu.do)

---

## 👨‍💻 Autor

**Micha Heredia**
🔗 [https://github.com/DmeshellHeredia](https://github.com/DmeshellHeredia)

---

## 🧩 Futuras mejoras

* Mejoras de UI/UX
* Más intents y cobertura semántica
* Deploy online (HuggingFace Spaces / Render)
* Integración con base de datos
* Logging y analytics

---

## 📜 Licencia

MIT License
