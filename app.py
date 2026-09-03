import os
import json
import copy
import random
import asyncio
import base64
import concurrent.futures
from io import BytesIO
import streamlit as st
from streamlit_lottie import st_lottie
from textblob import TextBlob
from gtts import gTTS

# Compatibilidad con la sintaxis de las diapositivas
st.lottie = st_lottie

# -----------------------------------------------------------------------------
# MOTORES DE VOZ NEURAL MASCULINA & TRADUCCIÓN
# -----------------------------------------------------------------------------
try:
    import edge_tts
    HAS_EDGE_TTS = True
except Exception:
    HAS_EDGE_TTS = False

try:
    from deep_translator import GoogleTranslator
    HAS_DEEP = True
except Exception:
    HAS_DEEP = False

try:
    from googletrans import Translator as GTrans
    HAS_GTRANS = True
except Exception:
    HAS_GTRANS = False


def run_async(coro):
    """Ejecuta corrutinas de forma segura sin colisionar con el bucle de eventos de Streamlit."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    else:
        return asyncio.run(coro)


def get_speech_audio(text: str, voice_name: str = "es-ES-AlvaroNeural") -> bytes:
    if not text or not text.strip():
        return b""

    # Voz masculina neural (edge-tts)
    if HAS_EDGE_TTS:
        try:
            async def _synthesize():
                comm = edge_tts.Communicate(text, voice_name)
                chunks = []
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        chunks.append(chunk["data"])
                return b"".join(chunks)

            audio_data = run_async(_synthesize())
            if audio_data:
                return audio_data
        except Exception:
            pass

    # Respaldo con gTTS
    try:
        tts = gTTS(text=text, lang="es", tld="es", slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return b""


def render_clean_html(html_str: str):
    """Elimina sangrías para evitar que Markdown interprete el HTML como código fuente."""
    clean = "".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Compañero Emocional // Cyber-Noir",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# -----------------------------------------------------------------------------
# CARGA Y SUPRESIÓN DE BOTONES DEL LOTTIE
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_lottie():
    search_dirs = []
    try:
        search_dirs.append(os.path.dirname(os.path.abspath(__file__)))
    except Exception:
        pass
    search_dirs.append(os.getcwd())
    search_dirs.append(".")

    filenames = [
        "AI robo.json",
        "graficos.json",
        "ai robo.json",
        "AI_robo.json",
        "ai_robo.json",
        "robot.json",
    ]

    loaded_json = None
    for sdir in search_dirs:
        if not sdir or not os.path.isdir(sdir):
            continue
        for fname in filenames:
            path = os.path.join(sdir, fname)
            if os.path.isfile(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and ("layers" in data or "v" in data):
                            loaded_json = data
                            break
                except Exception:
                    pass
        if loaded_json:
            break

    # Búsqueda recursiva en subdirectorios
    if not loaded_json:
        for sdir in search_dirs:
            if not sdir or not os.path.isdir(sdir):
                continue
            for root, _, files in os.walk(sdir):
                for f in files:
                    if f.lower().endswith(".json") and f.lower() not in ["package.json", "tsconfig.json"]:
                        try:
                            with open(os.path.join(root, f), "r", encoding="utf-8") as file_handle:
                                data = json.load(file_handle)
                                if isinstance(data, dict) and ("layers" in data or "v" in data):
                                    loaded_json = data
                                    break
                        except Exception:
                            continue
                if loaded_json:
                    break
            if loaded_json:
                break

    if not loaded_json:
        return None

    # Ocultar capas 1 a 10 (botones dibujados dentro del archivo JSON)
    clean_anim = copy.deepcopy(loaded_json)
    button_words = ["outlines", "think", "alert", "jump", "yes", "no"]
    clean_layers = []

    for layer in clean_anim.get("layers", []):
        name = str(layer.get("nm", "")).strip().lower()
        idx = layer.get("ind", 99)
        if idx <= 10 or any(word in name for word in button_words):
            layer["hd"] = True
            continue
        clean_layers.append(layer)

    clean_anim["layers"] = clean_layers
    return clean_anim


base_animation = load_and_clean_lottie()


def get_mood_slice(anim_data, marker: str):
    if not anim_data:
        return None

    sliced = copy.deepcopy(anim_data)
    total_frames = anim_data.get("op", 0)

    # Marcadores de las 5 funciones
    marker_ranges = {
        "idle": (0, 30),
        "yes": (31, 105),
        "no": (106, 180),
        "alert": (181, 270),
        "thinking": (271, 390),
        "jump": (391, 479),
    }

    if total_frames >= 400 and marker in marker_ranges:
        start_f, end_f = marker_ranges[marker]
        sliced["ip"] = start_f
        sliced["op"] = end_f

    return sliced


# -----------------------------------------------------------------------------
# TRADUCCIÓN
# -----------------------------------------------------------------------------
def translate_phrase(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    if not text or not text.strip():
        return ""
    if source_lang == target_lang:
        return text

    if HAS_DEEP:
        try:
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception:
            pass

    if HAS_GTRANS:
        try:
            src = "es" if source_lang == "auto" else source_lang
            return GTrans().translate(text, src=src, dest=target_lang).text
        except Exception:
            pass

    return text


# -----------------------------------------------------------------------------
# MENSAJES CONVERSACIONALES
# -----------------------------------------------------------------------------
CHISTES = [
    "—Papá, ¿qué se siente tener un hijo tan inteligente? —No sé hijo, pregúntale a tu abuelo.",
    "¿Qué le dice un bit a otro? —Nos vemos en el bus.",
    "¿Por qué los pájaros no usan WhatsApp? —Porque ya tienen Twitter.",
    "¿Cómo maldice un informático frustrado? —¡Me cago en el bit que te parió!",
    "¿Qué hace una abeja en el gimnasio? —¡Zumba!",
    "Tranquilo/a: hasta el código mejor optimizado falló decenas de veces antes de compilar.",
]

MOTIVACIONES = [
    "¡Qué alegría leerte así! Aprovecha este buen momento para darte un gusto, compartir tu alegría o avanzar en eso que tanto querías.",
    "¡Esa es la actitud! Con esa buena energía contagias a cualquiera. ¡Sigue disfrutando tu día al máximo!",
    "¡Se nota que las cosas van bien! Mantén ese optimismo y celebra tanto los pequeños como los grandes logros.",
]

CONSEJOS_CALMA = [
    "Uff, es normal sentirse así cuando las cosas salen mal o son injustas. Respira hondo, bebe un vaso de agua fresca y date cinco minutos antes de continuar.",
    "Comprendo tu molestia, a cualquiera le daría rabia. Date un pequeño respiro para despejarte; tu tranquilidad siempre es lo primero.",
    "A veces el día se pone cuesta arriba. Suelta la tensión un momento, estira los hombros y no permitas que esto te arruine el resto del día.",
]

CONVERSACION_NEUTRAL = [
    "Te escucho con atención. Los días tranquilos y en calma son ideales para reflexionar o simplemente descansar.",
    "Comprendo lo que dices. Cuéntame con confianza si quieres desahogarte o pensar en voz alta.",
]

# Palabras clave para activar las 5 funciones
JUMP_WORDS = ["gané", "logré", "triunfo", "increíble", "asombroso", "celebrar", "fiesta", "campeón", "victoria", "genial", "aprobé"]
YES_WORDS = ["bien", "feliz", "contento", "me gusta", "alegre", "gracias", "bueno", "excelente", "agradecido", "positivo"]
ALERT_WORDS = ["cuidado", "alerta", "estrés", "ansiedad", "nervioso", "preocupado", "urgente", "peligro", "tensión", "miedo", "ojo"]
NO_WORDS = ["no", "odio", "rabia", "molesto", "enojado", "pésimo", "terrible", "desastre", "triste", "mal", "asco", "horrible"]
THINK_WORDS = ["pensando", "quizás", "tal vez", "duda", "curioso", "analizando", "pregunto", "tranquilo", "calma", "depende"]


def analyze_conversation(user_text: str, polarity: float, subjectivity: float):
    lower_text = user_text.lower()

    # 1. JUMP -> Color Gradiente (Euforia / Éxito / Celebración)
    if any(k in lower_text for k in JUMP_WORDS) or polarity >= 0.55:
        return {
            "title": "¡Qué logro tan increíble, me alegro muchísimo!",
            "feeling": "¡Euforia y Gran Celebración!",
            "emoji": "🚀",
            "marker": "jump",
            "accent_color": "#00f0ff",
            "is_gradient": True,
            "glow": "rgba(255, 0, 127, 0.55)",
            "message": random.choice(MOTIVACIONES),
        }

    # 2. YES -> Verde (Afirmación / Alegría / Buena vibra)
    if any(k in lower_text for k in YES_WORDS) or polarity > 0.05:
        return {
            "title": "¡Qué gusto leerte, todo va por buen camino!",
            "feeling": "Afirmativo y Contento",
            "emoji": "😊",
            "marker": "yes",
            "accent_color": "#00ff88",  # Verde
            "is_gradient": False,
            "glow": "rgba(0, 255, 136, 0.5)",
            "message": random.choice(MOTIVACIONES),
        }

    # 3. ALERT -> Amarillo (Precaución / Tensión / Ansiedad)
    if any(k in lower_text for k in ALERT_WORDS) or (subjectivity > 0.65 and polarity < 0.1):
        return {
            "title": "Atención: Tómate una pausa y respira...",
            "feeling": "Alerta y Tensión",
            "emoji": "⚠️",
            "marker": "alert",
            "accent_color": "#ffd600",  # Amarillo
            "is_gradient": False,
            "glow": "rgba(255, 214, 0, 0.5)",
            "message": random.choice(CONSEJOS_CALMA),
        }

    # 4. NO -> Rojo (Negación / Rabia / Descontento / Tristeza)
    if any(k in lower_text for k in NO_WORDS) or polarity < -0.05:
        return {
            "title": "Un abrazo fuerte... no estás solo/a en esto",
            "feeling": "Negativa o Desánimo",
            "emoji": "🛑",
            "marker": "no",
            "accent_color": "#ff3344",  # Rojo
            "is_gradient": False,
            "glow": "rgba(255, 51, 68, 0.5)",
            "message": f"Comprendo que la situación no sea buena. Para sacarte aunque sea una sonrisa, mira este chiste:\n\n{random.choice(CHISTES)}",
        }

    # 5. THINKING -> Púrpura (Reflexión / Duda / Neutralidad)
    return {
        "title": "Te escucho con atención, vamos a analizarlo...",
        "feeling": "Pensativo y Reflexivo",
        "emoji": "🔮",
        "marker": "thinking",
        "accent_color": "#bf5af2",  # Púrpura
        "is_gradient": False,
        "glow": "rgba(191, 90, 242, 0.5)",
        "message": random.choice(CONVERSACION_NEUTRAL),
    }


# -----------------------------------------------------------------------------
# ESTADO DE SESIÓN (Para chips interactivos)
# -----------------------------------------------------------------------------
if "phrase_input" not in st.session_state:
    st.session_state.phrase_input = ""


def set_quick_phrase(phrase: str):
    st.session_state.phrase_input = phrase


# -----------------------------------------------------------------------------
# ENCABEZADO Y LOS 5 CHIPS RÁPIDOS
# -----------------------------------------------------------------------------
render_clean_html(
    """
    <div style="text-align: center; margin-top: 5px; margin-bottom: 18px;">
        <div class="title-glow">TU COMPAÑERO EMOCIONAL</div>
        <p style="color: #8da4be; font-size: 0.95rem; margin-top: 2px;">
            Escribe cómo te sientes o presiona Enter para una respuesta inmediata.
        </p>
    </div>
    """
)

# 5 Botones de prueba rápida para activar las 5 funciones del Lottie
render_clean_html(
    """
    <div style="text-align: center; margin-bottom: 12px;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64d2ff; letter-spacing: 2px; text-transform: uppercase;">
            ⚡ Pruebas rápidas (Las 5 funciones del Robot):
        </span>
    </div>
    """
)

chip_cols = st.columns(5)
with chip_cols[0]:
    if st.button("🚀 ¡Gané y triunfé!", use_container_width=True, help="Activa JUMP (Gradiente)"):
        set_quick_phrase("¡Gané el concurso y fue un logro increíble!")
        st.rerun()

with chip_cols[1]:
    if st.button("😊 Todo está bien", use_container_width=True, help="Activa YES (Verde)"):
        set_quick_phrase("Me siento muy feliz, todo va bien hoy.")
        st.rerun()

with chip_cols[2]:
    if st.button("⚠️ Mucho estrés", use_container_width=True, help="Activa ALERT (Amarillo)"):
        set_quick_phrase("Tengo mucha ansiedad y alerta por esta situación.")
        st.rerun()

with chip_cols[3]:
    if st.button("🛑 Es un desastre", use_container_width=True, help="Activa NO (Rojo)"):
        set_quick_phrase("No me gusta esto, es un pésimo desastre y tengo mucha ira")
        st.rerun()

with chip_cols[4]:
    if st.button("🔮 Pensando dudas", use_container_width=True, help="Activa THINKING (Púrpura)"):
        set_quick_phrase("Estoy pensando y analizando qué decisión tomar.")
        st.rerun()

st.write("")

# Controles de Entrada
col_input, col_target = st.columns([3.2, 1], gap="medium")

with col_input:
    user_phrase = st.text_input(
        label="¿Qué tienes en mente?",
        placeholder="Escribe lo que sientes y pulsa Enter...",
        key="phrase_input",
    )

with col_target:
    selected_lang = st.selectbox(
        label="Traducir a:",
        options=["en", "es", "fr", "ja", "de", "it", "pt"],
        format_func=lambda c: {
            "en": "🇬🇧 Inglés (EN)",
            "es": "🇪🇸 Español (ES)",
            "fr": "🇫🇷 Francés (FR)",
            "ja": "🇯🇵 Japonés (JA)",
            "de": "🇩🇪 Alemán (DE)",
            "it": "🇮🇹 Italiano (IT)",
            "pt": "🇵🇹 Portugués (PT)",
        }.get(c, c),
        index=0,
    )

# Procesamiento de sentimientos en tiempo real
if user_phrase and user_phrase.strip():
    english_txt = translate_phrase(user_phrase, source_lang="auto", target_lang="en")
    blob = TextBlob(english_txt)
    polarity_val = round(blob.sentiment.polarity, 2)
    subjectivity_val = round(blob.sentiment.subjectivity, 2)
    translated_display = translate_phrase(user_phrase, source_lang="auto", target_lang=selected_lang)
    response = analyze_conversation(user_phrase, polarity_val, subjectivity_val)
else:
    polarity_val = 0.0
    subjectivity_val = 0.0
    english_txt = ""
    translated_display = ""
    response = {
        "title": "¡Hola! ¿Cómo te encuentras hoy?",
        "feeling": "Esperando conversar",
        "emoji": "👋",
        "marker": "idle",
        "accent_color": "#00f0ff",
        "is_gradient": False,
        "glow": "rgba(0, 240, 255, 0.45)",
        "message": "Cuéntame lo que estás sintiendo o cómo estuvo tu día. Aquí estaré listo para acompañarte y responderte.",
    }

active_lottie = get_mood_slice(base_animation, response["marker"])

# Estilos de borde con soporte para gradientes dinámicos
if response["is_gradient"]:
    border_css = """
    border: 2px solid transparent !important;
    background: linear-gradient(rgba(11, 16, 28, 0.94), rgba(11, 16, 28, 0.94)) padding-box,
                linear-gradient(135deg, #ff007f, #7928ca, #00f0ff, #ffd600) border-box !important;
    """
else:
    border_css = f"""
    border: 2px solid {response['accent_color']} !important;
    background: rgba(11, 16, 28, 0.92) !important;
    """


# -----------------------------------------------------------------------------
# SOBRESATURACIÓN VISUAL // CSS DINÁMICO & ELEMENTOS 3D
# -----------------------------------------------------------------------------
NOIR_FULL_FX = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --mood-color: __COLOR__;
    --mood-glow: __GLOW__;
}

/* Transparencia total para dejar pasar el fondo animado */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #05070c !important;
    color: #e6edf5 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    overflow-x: hidden;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

.block-container {
    max-width: 1150px !important;
    padding-top: 1.8rem !important;
    padding-bottom: 2.5rem !important;
    margin: 0 auto !important;
    position: relative;
    z-index: 2;
}

/* Suelo 3D Cyber-Grid en perspectiva */
.cyber-grid-floor {
    position: fixed;
    bottom: 0;
    left: -50%;
    width: 200%;
    height: 48vh;
    background-image:
        linear-gradient(to right, rgba(100, 210, 255, 0.08) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(100, 210, 255, 0.08) 1px, transparent 1px);
    background-size: 50px 50px;
    transform: perspective(400px) rotateX(65deg);
    animation: gridMove 14s linear infinite;
    z-index: 1;
    pointer-events: none;
    opacity: 0.55;
    mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 85%);
    -webkit-mask-image: linear-gradient(to top, rgba(0,0,0,1) 0%, rgba(0,0,0,0) 85%);
}

@keyframes gridMove {
    0% { background-position: 0 0; }
    100% { background-position: 0 50px; }
}

/* Nebulosa ambiental de luz reactiva */
.mood-nebula {
    position: fixed;
    top: 25%;
    left: 28%;
    width: 650px;
    height: 650px;
    border-radius: 50%;
    background: radial-gradient(circle, var(--mood-glow) 0%, transparent 70%);
    filter: blur(85px);
    z-index: 1;
    pointer-events: none;
    animation: nebulaPulse 5s ease-in-out infinite alternate;
}

@keyframes nebulaPulse {
    0% { transform: scale(0.9) translate(-15px, -15px); opacity: 0.4; }
    100% { transform: scale(1.15) translate(15px, 15px); opacity: 0.75; }
}

.title-glow {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: 2px;
    background: linear-gradient(135deg, #ffffff 10%, var(--mood-color) 60%, #ffffff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 35px var(--mood-glow);
    margin-bottom: 4px;
    transition: all 0.5s ease;
}

/* Tarjeta izquierda (diálogo) con hover sobresaturado */
.card-noir-dialogue {
    position: relative;
    border-radius: 24px;
    padding: 26px;
    backdrop-filter: blur(20px);
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.8), 0 0 30px var(--mood-glow), inset 0 0 20px var(--mood-glow);
    transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    __BORDER_CSS__
}

.card-noir-dialogue:hover {
    transform: translateY(-6px) scale(1.01);
    box-shadow: 0 25px 65px rgba(0, 0, 0, 0.9), 0 0 55px var(--mood-glow), inset 0 0 30px var(--mood-glow);
    border-color: #ffffff !important;
}

/* CONTENEDOR DERECHO NATIVO: El robot queda 100% adentro del cuadro */
div[data-testid="stVerticalBlockBorderWrapper"] {
    position: relative !important;
    border-radius: 24px !important;
    padding: 20px 20px 16px 20px !important;
    backdrop-filter: blur(20px) !important;
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.8), 0 0 35px var(--mood-glow), inset 0 0 25px var(--mood-glow) !important;
    transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
    __BORDER_CSS__
}

div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    transform: translateY(-6px) scale(1.01) !important;
    box-shadow: 0 25px 65px rgba(0, 0, 0, 0.9), 0 0 60px var(--mood-glow), inset 0 0 35px var(--mood-glow) !important;
    border-color: #ffffff !important;
}

/* Centrado y resplandor para el widget de Lottie */
div[data-testid="stLottie"], iframe[title="streamlit_lottie.st_lottie"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 0 auto !important;
    filter: drop-shadow(0 0 28px var(--mood-glow));
    transition: filter 0.5s ease;
}

/* Botones rápidos interactivos con microanimación */
.stButton > button {
    background: rgba(13, 19, 33, 0.85) !important;
    border: 1px solid rgba(100, 210, 255, 0.25) !important;
    border-radius: 30px !important;
    color: #e4edf8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 8px 16px !important;
    transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.4) !important;
}

.stButton > button:hover {
    border-color: var(--mood-color) !important;
    box-shadow: 0 0 30px var(--mood-glow), inset 0 0 15px var(--mood-glow) !important;
    transform: translateY(-3px) scale(1.05) !important;
    color: #ffffff !important;
    text-shadow: 0 0 10px var(--mood-color) !important;
}

/* Campo de entrada */
.stTextInput input {
    background: rgba(13, 19, 33, 0.85) !important;
    border: 1.5px solid rgba(100, 210, 255, 0.25) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-size: 1.05rem !important;
    padding: 14px 18px !important;
    box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.7) !important;
}

.stTextInput input:focus {
    border-color: var(--mood-color) !important;
    box-shadow: 0 0 28px var(--mood-glow), inset 0 0 14px var(--mood-glow) !important;
}

/* Pedestal Holográfico 3D bajo el robot */
.holo-base {
    position: relative;
    width: 100%;
    height: 38px;
    margin-top: -24px;
    margin-bottom: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
    perspective: 600px;
}

.holo-emitter-beam {
    position: absolute;
    bottom: 0;
    width: 180px;
    height: 65px;
    background: radial-gradient(ellipse at bottom, var(--mood-glow) 0%, transparent 75%);
    filter: blur(10px);
    pointer-events: none;
}

.holo-ring-outer {
    position: absolute;
    width: 220px;
    height: 48px;
    border-radius: 50%;
    border: 2px dashed var(--mood-color);
    box-shadow: 0 0 22px var(--mood-color), inset 0 0 10px var(--mood-color);
    animation: spinClockwise 10s linear infinite;
    opacity: 0.85;
}

.holo-ring-inner {
    position: absolute;
    width: 140px;
    height: 30px;
    border-radius: 50%;
    border: 1.5px solid var(--mood-color);
    box-shadow: 0 0 16px var(--mood-color);
    animation: spinCounterClockwise 6s linear infinite;
    opacity: 0.95;
}

@keyframes spinClockwise {
    0% { transform: rotateX(75deg) rotateZ(0deg); }
    100% { transform: rotateX(75deg) rotateZ(360deg); }
}

@keyframes spinCounterClockwise {
    0% { transform: rotateX(75deg) rotateZ(360deg); }
    100% { transform: rotateX(75deg) rotateZ(0deg); }
}

/* Ecualizador de audio */
.audio-equalizer {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 22px;
    margin-right: 12px;
}

.audio-bar {
    width: 3.5px;
    background: var(--mood-color);
    box-shadow: 0 0 10px var(--mood-color);
    border-radius: 3px;
    animation: eqPulse 0.9s ease-in-out infinite alternate;
}

.audio-bar:nth-child(1) { height: 35%; animation-delay: 0.1s; }
.audio-bar:nth-child(2) { height: 95%; animation-delay: 0.3s; }
.audio-bar:nth-child(3) { height: 60%; animation-delay: 0.2s; }
.audio-bar:nth-child(4) { height: 100%; animation-delay: 0.4s; }
.audio-bar:nth-child(5) { height: 45%; animation-delay: 0.15s; }

@keyframes eqPulse {
    0% { transform: scaleY(0.35); }
    100% { transform: scaleY(1.15); }
}

/* Medidor visual de polaridad */
.gauge-track {
    position: relative;
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    margin: 8px 0;
    overflow: visible;
}

.gauge-pin {
    position: absolute;
    top: -5px;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #ffffff;
    border: 3px solid var(--mood-color);
    box-shadow: 0 0 18px var(--mood-color);
    transition: left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>

<!-- Elementos visuales 3D y de fondo -->
<div class="cyber-grid-floor"></div>
<div class="mood-nebula"></div>
""".replace("__COLOR__", response["accent_color"]).replace("__GLOW__", response["glow"]).replace("__BORDER_CSS__", border_css)

render_clean_html(NOIR_FULL_FX)


# -----------------------------------------------------------------------------
# INYECCIÓN DEL SCRIPT INTERACTIVO (MOUSE, CHISPAS, ONDAS DE CHOQUE Y CONSTELACIONES)
# -----------------------------------------------------------------------------
st.components.v1.html(
    r"""
    <script>
    (function() {
        let doc = document;
        let win = window;
        try {
            if (window.parent && window.parent.document) {
                doc = window.parent.document;
                win = window.parent;
            }
        } catch(e) {}

        // Canvas persistente en la ventana principal
        let canvas = doc.getElementById('noir-cyber-canvas');
        if (!canvas) {
            canvas = doc.createElement('canvas');
            canvas.id = 'noir-cyber-canvas';
            canvas.style.position = 'fixed';
            canvas.style.top = '0';
            canvas.style.left = '0';
            canvas.style.width = '100vw';
            canvas.style.height = '100vh';
            canvas.style.zIndex = '0';
            canvas.style.pointerEvents = 'none';
            doc.body.prepend(canvas);
        }

        const ctx = canvas.getContext('2d');
        let w = canvas.width = win.innerWidth;
        let h = canvas.height = win.innerHeight;

        win.addEventListener('resize', () => {
            w = canvas.width = win.innerWidth;
            h = canvas.height = win.innerHeight;
        });

        const particles = [];
        const trail = [];
        const shockwaves = [];
        let mouse = { x: -1000, y: -1000 };

        // 1. Estela de chispas reactiva al mouse
        win.addEventListener('mousemove', (e) => {
            mouse.x = e.clientX;
            mouse.y = e.clientY;
            for (let i = 0; i < 3; i++) {
                trail.push({
                    x: e.clientX + (Math.random() - 0.5) * 8,
                    y: e.clientY + (Math.random() - 0.5) * 8,
                    size: Math.random() * 3 + 1.2,
                    alpha: 1.0,
                    decay: Math.random() * 0.025 + 0.015,
                    vx: (Math.random() - 0.5) * 2,
                    vy: (Math.random() - 0.5) * 2 - 0.5
                });
            }
        });

        // 2. Ondas de choque y fuegos artificiales al hacer clic
        win.addEventListener('click', (e) => {
            for (let i = 0; i < 16; i++) {
                const angle = (Math.PI * 2 / 16) * i;
                const spd = Math.random() * 4 + 3;
                trail.push({
                    x: e.clientX,
                    y: e.clientY,
                    size: Math.random() * 4 + 2,
                    alpha: 1,
                    decay: 0.02,
                    vx: Math.cos(angle) * spd,
                    vy: Math.sin(angle) * spd
                });
            }
            shockwaves.push({
                x: e.clientX,
                y: e.clientY,
                radius: 10,
                maxRadius: 220,
                alpha: 1
            });
        });

        // Partículas del espacio cyber
        for (let i = 0; i < 65; i++) {
            particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                r: Math.random() * 2 + 0.7,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                alpha: Math.random() * 0.6 + 0.3
            });
        }

        function getThemeColor() {
            try {
                const col = doc.documentElement.style.getPropertyValue('--mood-color');
                if (col && col.trim()) return col.trim();
            } catch(e) {}
            return '#00f0ff';
        }

        function draw() {
            ctx.clearRect(0, 0, w, h);
            const col = getThemeColor();

            // Dibujar constelaciones
            for (let i = 0; i < particles.length; i++) {
                const p = particles[i];
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0) p.x = w;
                if (p.x > w) p.x = 0;
                if (p.y < 0) p.y = h;
                if (p.y > h) p.y = 0;

                // Enlace con el mouse
                const dm = Math.hypot(p.x - mouse.x, p.y - mouse.y);
                if (dm < 140) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(mouse.x, mouse.y);
                    ctx.strokeStyle = col;
                    ctx.globalAlpha = (1 - dm / 140) * 0.45;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                    ctx.globalAlpha = 1;
                }

                // Enlace entre nodos
                for (let j = i + 1; j < particles.length; j++) {
                    const p2 = particles[j];
                    const d = Math.hypot(p.x - p2.x, p.y - p2.y);
                    if (d < 120) {
                        ctx.beginPath();
                        ctx.moveTo(p.x, p.y);
                        ctx.lineTo(p2.x, p2.y);
                        ctx.strokeStyle = col;
                        ctx.globalAlpha = (1 - d / 120) * 0.25;
                        ctx.lineWidth = 0.8;
                        ctx.stroke();
                        ctx.globalAlpha = 1;
                    }
                }

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = col;
                ctx.shadowBlur = 10;
                ctx.shadowColor = col;
                ctx.globalAlpha = p.alpha;
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            // Ondas de choque
            for (let i = shockwaves.length - 1; i >= 0; i--) {
                const sw = shockwaves[i];
                sw.radius += 5;
                sw.alpha -= 0.022;
                if (sw.alpha <= 0 || sw.radius >= sw.maxRadius) {
                    shockwaves.splice(i, 1);
                    continue;
                }
                ctx.beginPath();
                ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
                ctx.strokeStyle = col;
                ctx.globalAlpha = sw.alpha * 0.8;
                ctx.lineWidth = 2.5;
                ctx.shadowBlur = 20;
                ctx.shadowColor = col;
                ctx.stroke();
                ctx.globalAlpha = 1;
            }

            // Chispas del cursor
            for (let i = trail.length - 1; i >= 0; i--) {
                const t = trail[i];
                t.x += t.vx;
                t.y += t.vy;
                t.alpha -= t.decay;
                if (t.alpha <= 0) {
                    trail.splice(i, 1);
                    continue;
                }
                ctx.beginPath();
                ctx.arc(t.x, t.y, t.size, 0, Math.PI * 2);
                ctx.fillStyle = col;
                ctx.globalAlpha = t.alpha;
                ctx.shadowBlur = 14;
                ctx.shadowColor = col;
                ctx.fill();
                ctx.globalAlpha = 1;
            }

            win.requestAnimationFrame(draw);
        }
        draw();
    })();
    </script>
    """,
    height=0,
    width=0,
)


# -----------------------------------------------------------------------------
# ESCENARIO PRINCIPAL: DIÁLOGO (IZQUIERDA) & ROBOT CONTENIDO (DERECHA)
# -----------------------------------------------------------------------------
col_dialogo, col_robo = st.columns([1.25, 1], gap="large")

# COLUMNA IZQUIERDA: DIÁLOGO Y RESPUESTA
with col_dialogo:
    render_clean_html(
        f"""
        <div class="card-noir-dialogue">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="color: {response['accent_color']}; font-family: 'Orbitron'; font-size: 0.85rem; font-weight: 800; letter-spacing: 1.5px;">
                    {response['emoji']} TU COMPAÑERO DICE
                </span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: rgba(0,0,0,0.4); padding: 5px 12px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); color: #c4d7ec;">
                    Subjetividad: {int(subjectivity_val * 100)}%
                </span>
            </div>

            <h2 style="font-size: 1.6rem; font-weight: 700; margin: 0 0 12px 0; color: #ffffff; text-shadow: 0 0 18px var(--mood-glow);">
                {response['title']}
            </h2>

            <div style="font-size: 1.05rem; line-height: 1.6; color: #edf4fc; background: rgba(0,0,0,0.35); padding: 18px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px;">
                {response['message'].replace(chr(10), '<br>')}
            </div>
        </div>
        """
    )

    # Audio con reproducción automática y voz masculina neural
    if user_phrase and user_phrase.strip():
        selected_male_voice = st.session_state.get("preferred_voice", "es-ES-AlvaroNeural")
        spoken_text = f"{response['title']}. {response['message']}"
        voice_audio = get_speech_audio(spoken_text, voice_name=selected_male_voice)

        if voice_audio:
            render_clean_html(
                f"""
                <div style="display: flex; align-items: center; margin-top: 6px; margin-bottom: 6px;">
                    <div class="audio-equalizer">
                        <div class="audio-bar"></div>
                        <div class="audio-bar"></div>
                        <div class="audio-bar"></div>
                        <div class="audio-bar"></div>
                        <div class="audio-bar"></div>
                    </div>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #8da4be;">
                        Voz neural activa (reproducción automática)
                    </span>
                </div>
                """
            )
            try:
                st.audio(voice_audio, format="audio/mp3", autoplay=True)
            except TypeError:
                b64_audio = base64.b64encode(voice_audio).decode("utf-8")
                render_clean_html(
                    f"""
                    <audio autoplay controls style="width: 100%; height: 38px; border-radius: 10px; margin-top: 4px;">
                        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
                    </audio>
                    """
                )

    # Traducción Multilingüe
    if translated_display:
        render_clean_html(
            f"""
            <div style="background: rgba(100, 210, 255, 0.05); border-radius: 14px; padding: 12px 18px; border: 1.5px solid {response['accent_color']}; box-shadow: 0 0 20px var(--mood-glow); margin-top: 10px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: {response['accent_color']}; letter-spacing: 1.5px;">
                    TRADUCCIÓN ({selected_lang.upper()}):
                </div>
                <div style="font-size: 0.95rem; color: #ffffff; margin-top: 3px;">
                    "{translated_display}"
                </div>
            </div>
            """
        )


# COLUMNA DERECHA: GRÁFICO LOTTIE 100% CONTENIDO EN SU CUADRO
with col_robo:
    with st.container(border=True):
        # Cabecera de telemetría del robot
        render_clean_html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; width: 100%;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: {response['accent_color']}; letter-spacing: 2px;">
                    ● RADAR ACTIVO
                </span>
                <span style="font-size: 0.85rem; font-weight: 700; color: #ffffff;">
                    {response['emoji']} {response['feeling']}
                </span>
            </div>
            """
        )

        # Gráfico del robot
        if active_lottie:
            st.lottie(
                active_lottie,
                width=270,
                height=270,
                key=f"hologram_robot_{response['marker']}",
            )
        else:
            st.info("Buscando animación Lottie...")

        # Pedestal Holográfico 3D (anillos giratorios + haz de luz bajo el robot)
        render_clean_html(
            """
            <div class="holo-base">
                <div class="holo-emitter-beam"></div>
                <div class="holo-ring-outer"></div>
                <div class="holo-ring-inner"></div>
            </div>
            """
        )

        # Medidor visual de polaridad interactivo
        pin_percent = int(((polarity_val + 1.0) / 2.0) * 100)
        pin_percent = max(0, min(100, pin_percent))

        render_clean_html(
            f"""
            <div style="margin-top: 4px; padding: 0 4px; width: 100%;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-family: 'JetBrains Mono'; color: #7f97b2;">
                    <span>Negativo (-1.0)</span>
                    <span style="color: {response['accent_color']}; font-weight: 700;">Ánimo: {polarity_val:+0.2f}</span>
                    <span>Positivo (+1.0)</span>
                </div>
                <div class="gauge-track">
                    <div class="gauge-pin" style="left: calc({pin_percent}% - 9px);"></div>
                </div>
            </div>
            """
        )


# -----------------------------------------------------------------------------
# BARRA LATERAL
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎙️ Configuración de Voz")
    voice_options = {
        "es-ES-AlvaroNeural": "Voz Masculina (Álvaro - España)",
        "es-MX-JorgeNeural": "Voz Masculina (Jorge - México)",
        "es-CO-GonzaloNeural": "Voz Masculina (Gonzalo - Colombia)",
        "es-AR-TomasNeural": "Voz Masculina (Tomás - Argentina)",
    }
    st.selectbox(
        label="Selecciona la voz:",
        options=list(voice_options.keys()),
        format_func=lambda v: voice_options[v],
        key="preferred_voice",
    )

    st.markdown("---")
    st.markdown("### 🔮 Espectro Emocional")
    st.info(
        """
        - **JUMP (Gradiente Multicolor):** Euforia, victoria y celebración.
        - **YES (Verde):** Alegría, positivismo y motivación.
        - **ALERT (Amarillo):** Precaución, estrés o tensión.
        - **NO (Rojo):** Desánimo, tristeza o descontento.
        - **THINKING (Púrpura):** Curiosidad, duda o reflexión.
        """
    )
    st.caption("NOIR.AI // Python 3.11 // Full Cyber-Noir FX")
