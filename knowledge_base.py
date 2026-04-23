"""
ITLA Knowledge Base
All chatbot content lives here. Each intent follows a strict schema so the
matching engine can treat every entry uniformly.

Schema
------
name          : str   – unique snake_case identifier
category      : str   – grouping label
keywords      : list  – high-signal words used for keyword scoring
required_words: list  – ALL of these must be present for a keyword match
variants      : list  – natural-language phrasings (drives fuzzy + semantic)
response      : str   – primary, concise answer
extended      : str   – longer answer (used when confidence is medium)
source        : str   – reference URL or note
"""

INTENTS: list[dict] = [
    # ── 1. SALUDO ──────────────────────────────────────────────────────────────
    {
        "name": "saludo",
        "category": "general",
        "keywords": ["hola", "buenas", "buenos", "saludos", "hey", "klk", "qué tal", "qué hay"],
        "required_words": [],
        "variants": [
            "hola",
            "buenas",
            "buenos días",
            "buenas tardes",
            "buenas noches",
            "saludos",
            "hey",
            "klk",
            "qué tal",
            "qué hay",
            "hola cómo estás",
            "buen día",
        ],
        "response": (
            "¡Hola! 👋 Soy el asistente virtual del **ITLA**.\n\n"
            "Puedo ayudarte con información sobre:\n"
            "- 📚 Oferta académica\n"
            "- 📝 Inscripción\n"
            "- 📍 Ubicación y sedes\n"
            "- 📞 Contacto\n"
            "- 💻 Acceso a plataforma\n\n"
            "¿En qué te puedo ayudar?"
        ),
        "extended": None,
        "source": "N/A",
    },

    # ── 2. QUÉ ES EL ITLA ──────────────────────────────────────────────────────
    {
        "name": "que_es_itla",
        "category": "institucional",
        "keywords": ["itla", "instituto", "tecnológico", "américas", "qué es", "quiénes son", "institución", "misión", "visión"],
        "required_words": [],
        "variants": [
            "qué es el itla",
            "qué es itla",
            "quiénes son",
            "cuéntame sobre el itla",
            "información sobre el itla",
            "qué hace el itla",
            "misión del itla",
            "visión del itla",
            "de qué trata el itla",
            "itla que es",
            "para qué sirve el itla",
            "háblame del itla",
        ],
        "response": (
            "El **ITLA** (Instituto Tecnológico de Las Américas) es una institución de educación superior "
            "técnica de la República Dominicana, enfocada en tecnología de la información, electrónica y "
            "administración de sistemas.\n\n"
            "Forma técnicos y tecnólogos con perfil práctico y orientado al mercado laboral. "
            "Opera bajo el Ministerio de Educación Superior, Ciencia y Tecnología (MESCyT)."
        ),
        "extended": (
            "El **Instituto Tecnológico de Las Américas (ITLA)** fue creado como parte de la política "
            "de modernización tecnológica de la República Dominicana. Su misión es formar profesionales "
            "técnicos altamente calificados en áreas de tecnología, brindando educación de calidad con "
            "enfoque práctico. Ofrece programas de grado técnico y tecnológico, así como educación "
            "continua y certificaciones internacionales."
        ),
        "source": "https://www.itla.edu.do",
    },

    # ── 3. UBICACIÓN ───────────────────────────────────────────────────────────
    {
        "name": "ubicacion",
        "category": "contacto",
        "keywords": ["ubicación", "dirección", "donde", "están", "queda", "localización", "mapa", "cómo llegar"],
        "required_words": [],
        "variants": [
            "dónde están ubicados",
            "cuál es la dirección",
            "dónde queda el itla",
            "cómo llegar al itla",
            "dirección del itla",
            "ubicación del itla",
            "dónde está el itla",
            "mapa del itla",
            "localización",
            "en qué sector está",
            "dónde los encuentro",
        ],
        "response": (
            "📍 **Sede Central ITLA**\n"
            "Autopista Duarte Km. 16½, Los Alcarrizos,\n"
            "Santo Domingo Oeste, República Dominicana.\n\n"
            "El ITLA también cuenta con sedes regionales en distintas provincias del país. "
            "Escribe *sedes* para ver la lista completa."
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/contacto",
    },

    # ── 4. TELÉFONO / CONTACTO ─────────────────────────────────────────────────
    {
        "name": "telefono",
        "category": "contacto",
        "keywords": ["teléfono", "número", "llamar", "contacto", "comunicarse", "línea", "whatsapp"],
        "required_words": [],
        "variants": [
            "cuál es el teléfono",
            "número de contacto",
            "cómo los llamo",
            "cómo me comunico",
            "teléfono del itla",
            "número del itla",
            "línea de contacto",
            "tienen whatsapp",
            "cómo puedo llamarlos",
            "número de teléfono",
            "quiero llamar al itla",
        ],
        "response": (
            "📞 **Contacto ITLA**\n\n"
            "- **Teléfono:** (809) 530-4852\n"
            "- **Fax:** (809) 530-4851\n"
            "- **Horario:** Lunes a viernes, 8:00 AM – 5:00 PM\n\n"
            "También puedes contactarlos por correo o en la plataforma oficial."
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/contacto",
    },

    # ── 5. CORREO ──────────────────────────────────────────────────────────────
    {
        "name": "correo",
        "category": "contacto",
        "keywords": ["correo", "email", "mail", "electrónico", "escribir", "mensaje"],
        "required_words": [],
        "variants": [
            "cuál es el correo",
            "correo del itla",
            "email del itla",
            "dirección de correo",
            "cómo les escribo",
            "correo electrónico",
            "a qué email les escribo",
            "quiero enviar un correo",
            "correo de contacto",
            "mail del itla",
        ],
        "response": (
            "📧 **Correos ITLA**\n\n"
            "- **General:** info@itla.edu.do\n"
            "- **Admisiones:** admisiones@itla.edu.do\n"
            "- **Soporte técnico:** soporte@itla.edu.do\n\n"
            "Tiempo de respuesta habitual: 1–2 días hábiles."
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/contacto",
    },

    # ── 6. OFERTA ACADÉMICA ────────────────────────────────────────────────────
    {
        "name": "oferta_academica",
        "category": "academico",
        "keywords": ["carrera", "carreras", "programa", "programas", "oferta", "academica", "estudiar", "tecnologia", "grado", "software", "desarrollo", "programacion", "sistemas", "ingenieria", "aprender", "interesado"],
        "required_words": [],
        "variants": [
            "qué carreras ofrecen",
            "qué programas tienen",
            "oferta académica",
            "qué se puede estudiar en el itla",
            "carreras disponibles",
            "cuáles son los programas",
            "qué tecnologías enseñan",
            "cuáles carreras hay",
            "lista de carreras",
            "programas de grado",
            "qué puedo estudiar",
            "tienen ingeniería",
            "quiero estudiar desarrollo de software",
            "estoy interesado en estudiar en el itla",
            "interesado en desarrollo de software",
            "estudiar programación en el itla",
            "carrera de sistemas",
        ],
        "response": (
            "📚 **Oferta Académica ITLA**\n\n"
            "**Tecnologías (grado técnico/tecnológico):**\n"
            "- 💻 Desarrollo de Software\n"
            "- 🌐 Redes y Telecomunicaciones\n"
            "- 🔌 Electrónica y Automatización\n"
            "- 🎨 Multimedia y Diseño Digital\n"
            "- 🛡️ Ciberseguridad\n"
            "- 📊 Soporte y Administración de Sistemas\n"
            "- 📱 Desarrollo de Aplicaciones Móviles\n\n"
            "Para ver el pensum completo: [itla.edu.do/oferta-academica](https://www.itla.edu.do)"
        ),
        "extended": (
            "El ITLA ofrece programas de **grado técnico** (2 años) y **tecnológico** (3 años) en áreas "
            "de tecnología de la información, electrónica y afines. Los programas están diseñados con "
            "enfoque práctico y alineados con las demandas del mercado laboral dominicano e internacional. "
            "Muchos programas incluyen preparación para certificaciones internacionales como CompTIA, Cisco, "
            "Oracle, entre otras."
        ),
        "source": "https://www.itla.edu.do/oferta-academica",
    },

    # ── 7. INSCRIPCIÓN ─────────────────────────────────────────────────────────
    {
        "name": "inscripcion",
        "category": "academico",
        "keywords": ["inscripcion", "inscribirse", "inscribir", "inscribo", "inscribirme",
                     "matricula", "admision", "requisitos", "documentos", "registro",
                     "ingresar", "matricular", "entrar", "semestre"],
        "required_words": [],
        "variants": [
            "cómo me inscribo",
            "cómo es el proceso de inscripción",
            "qué documentos necesito",
            "proceso de admisión",
            "cómo puedo entrar al itla",
            "requisitos para inscribirse",
            "cuándo abren inscripciones",
            "quiero inscribirme",
            "cómo matricularse",
            "pasos para ingresar",
            "qué necesito para inscribirme",
            "inscripción online",
            "cómo inscribirme en el itla",
            "quiero inscribirme en el itla",
            "inscribirme en el itla este semestre",
            "cómo me matriculo en el itla",
        ],
        "response": (
            "📝 **Proceso de Inscripción ITLA**\n\n"
            "**Requisitos generales:**\n"
            "1. Acta de nacimiento (original)\n"
            "2. Diploma de bachillerato o certificado\n"
            "3. Fotografías 2×2\n"
            "4. Cédula de identidad (o pasaporte)\n"
            "5. Pago de matrícula\n\n"
            "**Pasos:**\n"
            "1. Completar formulario en [itla.edu.do](https://www.itla.edu.do)\n"
            "2. Entregar documentos en admisiones\n"
            "3. Realizar prueba de admisión (si aplica)\n"
            "4. Confirmar matrícula\n\n"
            "Para fechas de inscripción activas, visita el sitio oficial o llama al (809) 530-4852."
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/admisiones",
    },

    # ── 8. EDUCACIÓN CONTINUA ──────────────────────────────────────────────────
    {
        "name": "educacion_continua",
        "category": "academico",
        "keywords": ["educacion", "continua", "cursos", "certificacion", "taller", "diplomado", "capacitacion", "corta", "profesional", "cisco", "comptia", "oracle", "microsoft", "bootcamp", "certificar"],
        "required_words": [],
        "variants": [
            "qué cursos cortos tienen",
            "educación continua",
            "tienen certificaciones",
            "cursos de capacitación",
            "talleres disponibles",
            "diplomados del itla",
            "cursos profesionales",
            "quiero hacer un curso corto",
            "cursos sin inscripción formal",
            "formación continua",
            "cursos para profesionales",
            "tienen bootcamps",
            "tienen programa de certificación en cisco",
            "certificación en comptia",
            "cursos de cisco",
            "cursos de oracle",
            "programa de certificación internacional",
        ],
        "response": (
            "🎓 **Educación Continua ITLA**\n\n"
            "Ofrecen programas de corta duración para profesionales y público general:\n\n"
            "- **Certificaciones internacionales** (Cisco, CompTIA, Oracle, Microsoft)\n"
            "- **Diplomados tecnológicos**\n"
            "- **Talleres prácticos**\n"
            "- **Bootcamps de programación**\n"
            "- **Cursos en línea**\n\n"
            "📩 Para el catálogo actualizado: educacioncontinua@itla.edu.do\n"
            "🌐 [itla.edu.do/educacion-continua](https://www.itla.edu.do)"
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/educacion-continua",
    },

    # ── 9. SOPORTE TÉCNICO ─────────────────────────────────────────────────────
    {
        "name": "soporte",
        "category": "servicios",
        "keywords": ["soporte", "técnico", "ayuda", "problema", "falla", "sistema", "cuenta", "contraseña", "acceso"],
        "required_words": [],
        "variants": [
            "necesito soporte técnico",
            "tengo un problema con mi cuenta",
            "no puedo entrar al sistema",
            "olvidé mi contraseña",
            "cómo recupero mi acceso",
            "problema técnico",
            "sistema caído",
            "fallo en la plataforma",
            "soporte estudiantil",
            "ayuda con mi usuario",
            "reset de contraseña",
            "no me deja entrar",
        ],
        "response": (
            "🛠️ **Soporte Técnico ITLA**\n\n"
            "- **Email:** soporte@itla.edu.do\n"
            "- **Teléfono:** (809) 530-4852 ext. soporte\n"
            "- **Horario:** Lunes a viernes, 8:00 AM – 5:00 PM\n\n"
            "**Para recuperar contraseña:**\n"
            "1. Entra a [moodle.itla.edu.do](https://moodle.itla.edu.do)\n"
            "2. Haz clic en *¿Olvidaste tu contraseña?*\n"
            "3. Ingresa tu correo institucional\n\n"
            "Si el problema persiste, escribe directamente a soporte."
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/soporte",
    },

    # ── 10. SEDES ──────────────────────────────────────────────────────────────
    {
        "name": "sedes",
        "category": "contacto",
        "keywords": ["sede", "sedes", "campus", "regional", "provincia", "sucursal", "extensión"],
        "required_words": [],
        "variants": [
            "cuántas sedes tienen",
            "en qué provincias están",
            "sede regional",
            "campus del itla",
            "tienen sede en santiago",
            "sedes del itla",
            "hay itla en mi ciudad",
            "extensiones del itla",
            "itla en el norte",
            "sucursales del itla",
            "dónde más están",
            "ubicaciones del itla",
        ],
        "response": (
            "🗺️ **Sedes ITLA**\n\n"
            "**Sede Central:**\n"
            "📍 Autopista Duarte Km. 16½, Los Alcarrizos, Santo Domingo Oeste\n\n"
            "**Sedes Regionales:**\n"
            "- 🏫 Santiago\n"
            "- 🏫 San Pedro de Macorís\n"
            "- 🏫 La Vega\n"
            "- 🏫 San Francisco de Macorís\n"
            "- 🏫 Barahona\n"
            "- 🏫 Higüey\n\n"
            "Para direcciones exactas de cada sede, visita [itla.edu.do/sedes](https://www.itla.edu.do)."
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/sedes",
    },

    # ── 11. PLATAFORMA / MOODLE ────────────────────────────────────────────────
    {
        "name": "plataforma",
        "category": "servicios",
        "keywords": ["plataforma", "moodle", "virtual", "aula", "online", "campus", "usuario", "login", "recuperar", "contrasena", "entrar", "acceso", "cursos"],
        "required_words": [],
        "variants": [
            "cómo accedo a la plataforma",
            "dónde entro a moodle",
            "acceso al campus virtual",
            "aula virtual del itla",
            "cómo entro a mis clases",
            "link de la plataforma",
            "sistema de gestión académica",
            "plataforma estudiantil",
            "clases en línea",
            "campus online",
            "dónde veo mis cursos",
            "sistema de notas",
            "cómo recupero mi usuario",
            "recuperar usuario campus virtual",
            "olvidé mi usuario del sistema",
            "entrar al campus virtual",
            "cómo entro al campus virtual con mi usuario",
        ],
        "response": (
            "💻 **Plataforma Virtual ITLA**\n\n"
            "Accede al aula virtual (Moodle) en:\n"
            "🔗 [moodle.itla.edu.do](https://moodle.itla.edu.do)\n\n"
            "**Para iniciar sesión:**\n"
            "- Usuario: tu matrícula estudiantil\n"
            "- Contraseña: asignada por admisiones\n\n"
            "¿Problemas para entrar? Escribe *soporte* para obtener ayuda."
        ),
        "extended": None,
        "source": "https://moodle.itla.edu.do",
    },

    # ── 12. COSTOS / BECA ──────────────────────────────────────────────────────
    {
        "name": "costos_becas",
        "category": "academico",
        "keywords": ["costo", "precio", "beca", "becas", "gratuito", "gratis", "pago",
                     "financiamiento", "matricula"],
        "required_words": [],
        "variants": [
            "cuánto cuesta estudiar",
            "tiene costo el itla",
            "hay becas disponibles",
            "el itla es gratis",
            "cómo aplico a una beca",
            "precio de las carreras",
            "costo de matrícula",
            "financiamiento estudiantil",
            "beca del estado",
            "itla es gratuito",
            "quiero una beca",
            "cuánto cuesta la carrera",
        ],
        "response": (
            "💰 **Costos y Becas ITLA**\n\n"
            "El ITLA es una institución de **educación pública** con costos accesibles, "
            "subsidiada parcialmente por el Estado dominicano.\n\n"
            "**Becas disponibles:**\n"
            "- Beca Presidencial\n"
            "- Beca ITLA por rendimiento académico\n"
            "- Convenios con empresas privadas\n\n"
            "Para montos exactos y disponibilidad de becas, contacta a admisiones:\n"
            "📧 admisiones@itla.edu.do | 📞 (809) 530-4852"
        ),
        "extended": None,
        "source": "https://www.itla.edu.do/admisiones",
    },

    # ── 13. DESPEDIDA ──────────────────────────────────────────────────────────
    {
        "name": "despedida",
        "category": "general",
        "keywords": ["adiós", "bye", "hasta luego", "chao", "gracias", "muchas gracias", "ya fue", "eso es todo"],
        "required_words": [],
        "variants": [
            "adiós",
            "hasta luego",
            "chao",
            "bye",
            "gracias por la ayuda",
            "muchas gracias",
            "eso es todo",
            "ya no necesito más",
            "hasta pronto",
            "me voy",
            "listo gracias",
        ],
        "response": (
            "¡Con gusto! 😊 Si necesitas más información sobre el ITLA, aquí estaré.\n\n"
            "Visita el sitio oficial: [itla.edu.do](https://www.itla.edu.do)\n"
            "¡Mucho éxito! 🎓"
        ),
        "extended": None,
        "source": "N/A",
    },
]

# ── Quick-access index ─────────────────────────────────────────────────────────
INTENT_MAP: dict[str, dict] = {intent["name"]: intent for intent in INTENTS}