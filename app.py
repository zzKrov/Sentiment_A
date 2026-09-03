import os
import json
import base64
from io import BytesIO
import streamlit as st
from textblob import TextBlob
from gtts import gTTS

# Translation handling with resilient fallback
try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False

try:
    from googletrans import Translator as GoogleTransTranslator
    HAS_GOOGLETRANS = True
except ImportError:
    HAS_GOOGLETRANS = False

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & NOIR THEME SETUP
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NOIR.AI // Sentiment Companion",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load the local Lottie animation JSON
LOTTIE_FILE = "AI robo.json"
lottie_data = None
if os.path.exists(LOTTIE_FILE):
    try:
        with open(LOTTIE_FILE, "r", encoding="utf-8") as f:
            lottie_data = json.load(f)
    except Exception:
        lottie_data = None


# -----------------------------------------------------------------------------
# TRANSLATION UTILITY
# -----------------------------------------------------------------------------
def translate_text(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """Translates text reliably with deep-translator, googletrans, or fallback."""
    if not text.strip():
        return ""
    if source_lang == target_lang:
        return text

    # Attempt 1: deep-translator
    if HAS_DEEP_TRANSLATOR:
        try:
            return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        except Exception:
            pass

    # Attempt 2: googletrans
    if HAS_GOOGLETRANS:
        try:
            src = "es" if source_lang == "auto" else source_lang
            res = GoogleTransTranslator().translate(text, src=src, dest=target_lang)
            return res.text
        except Exception:
            pass

    return text


def generate_audio_base64(text: str, lang: str = "es") -> str:
    """Generates an in-memory base64 audio string using gTTS."""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        b64 = base64.b64encode(fp.read()).decode("utf-8")
        return f"data:audio/mp3;base64,{b64}"
    except Exception:
        return ""


# -----------------------------------------------------------------------------
# MOOD & BEHAVIORAL PROTOCOLS
# -----------------------------------------------------------------------------
ANGER_KEYWORDS = [
    "odio", "rabia", "furioso", "enojado", "enojada", "molesto", "molesta", "ira",
    "asqueroso", "maldito", "maldita", "angry", "furious", "hate", "mad", "pissed",
    "rage", "annoyed", "irritated", "stupid", "idiot"
]

EXCITED_KEYWORDS = [
    "increíble", "asombroso", "genial", "excelente", "vamos", "fuego", "logro",
    "triunfo", "campeón", "victoria", "awesome", "amazing", "let's go", "pumped",
    "hyped", "thrilled", "conquer", "jump", "power"
]

SAD_JOKES = [
    "¿Qué le dice un bit a otro? —Nos vemos en el bus.",
    "¿Por qué los pájaros no usan WhatsApp? —Porque ya tienen Twitter.",
    "¿Cómo maldice un informático? —¡Me cago en el bit que te parió!",
    "—Papá, ¿qué se siente tener un hijo tan guapo? —No sé, hijo, pregúntale a tu abuelo.",
    "¿Qué hace una abeja en el gimnasio? —¡Zumba!",
    "No te preocupes por el fracaso de hoy: hasta el mejor algoritmo tuvo que depurar cientos de errores."
]

MOTIVATIONS = [
    "¡Tu energía es arrolladora! Transforma este impulso en tu mayor conquista del día.",
    "¡El momento de acelerar es ahora! Cada segundo invertido con esta pasión crea historia.",
    "¡Estás en la cima de tu frecuencia! Toma esa idea que postergabas y ejecútala de inmediato.",
    "El fuego que sientes no es casualidad: es tu mente preparándose para romper límites."
]

CHILL_ADVICES = [
    "Respira hondo: Inhala en 4 segundos... Mantén 4... Exhala en 6. El control vuelve a ti.",
    "La furia es fuego que quema primero al que lo sostiene. Suelta la llama, observa con mente fría.",
    "Nada merece tu paz interior. Toma un vaso de agua, aléjate de la pantalla 2 minutos y retoma el timón.",
    "La calma no es debilidad; es la máxima demostración de poder táctico ante el caos."
]

NEUTRAL_PROMPTS = [
    "El silencio y el equilibrio son el lienzo donde nacen las ideas más profundas.",
    "¿Sabías que una mente neutral procesa 3 veces más opciones estratégicas que una mente reactiva?",
    "Estado Zen detectado. Excelente momento para analizar tus objetivos sin sesgos emocionales.",
    "La neutralidad es elegancia pura. Observar sin juzgar es una habilidad de pocos."
]


def detect_mood_and_protocol(user_text_orig: str, polarity: float, subjectivity: float):
    """
    Classifies the user's emotional state, selects a Lottie animation marker,
    and constructs a companion reaction protocol.
    """
    text_lower = user_text_orig.lower()

    # Priority 1: High stress / Anger
    if any(k in text_lower for k in ANGER_KEYWORDS) or (polarity < -0.3 and subjectivity > 0.6):
        import random
        return {
            "mood_id": "angry",
            "mood_name": "Alerta / Tensión Elevada",
            "emoji": "⚡",
            "marker": "alert",
            "color_theme": "#ff0055",
            "bg_glow": "rgba(255, 0, 85, 0.25)",
            "action_title": "Protocolo de Desescalada & Calma",
            "action_content": random.choice(CHILL_ADVICES),
            "status_text": "Sistemas en alerta térmica. Iniciando enfriamiento y equilibrio."
        }

    # Priority 2: Joy / Motivated / Peak Positive
    if any(k in text_lower for k in EXCITED_KEYWORDS) or (polarity >= 0.55):
        import random
        return {
            "mood_id": "excited",
            "mood_name": "Éxtasis / Alta Vibración",
            "emoji": "🚀",
            "marker": "jump",
            "color_theme": "#00ffcc",
            "bg_glow": "rgba(0, 255, 204, 0.25)",
            "action_title": "Protocolo Catalizador de Acción",
            "action_content": random.choice(MOTIVATIONS),
            "status_text": "Propulsores al 100%. Momento óptimo para crear y accionar."
        }

    # Priority 3: Cheerful / Positive
    if polarity > 0.05:
        import random
        return {
            "mood_id": "positive",
            "mood_name": "Positivo / Armónico",
            "emoji": "✨",
            "marker": "yes",
            "color_theme": "#00e5ff",
            "bg_glow": "rgba(0, 229, 255, 0.25)",
            "action_title": "Protocolo de Refuerzo Positivo",
            "action_content": random.choice(MOTIVATIONS),
            "status_text": "Frecuencia armónica detectada. Flujo creativo activado."
        }

    # Priority 4: Sadness / Melancholy
    if polarity < -0.05:
        import random
        return {
            "mood_id": "sad",
            "mood_name": "Melancolía / Baja Frecuencia",
            "emoji": "🌧️",
            "marker": "no",
            "color_theme": "#bd00ff",
            "bg_glow": "rgba(189, 0, 255, 0.25)",
            "action_title": "Protocolo Reanimador // Chiste Cuántico",
            "action_content": random.choice(SAD_JOKES),
            "status_text": "Resonancia baja detectada. Desplegando contramedidas de optimismo."
        }

    # Priority 5: Neutral / Contemplative
    import random
    return {
        "mood_id": "neutral",
        "mood_name": "Neutro / Contemplativo",
        "emoji": "🔮",
        "marker": "thinking",
        "color_theme": "#00f0ff",
        "bg_glow": "rgba(0, 240, 255, 0.2)",
        "action_title": "Protocolo de Reflexión Sintética",
        "action_content": random.choice(NEUTRAL_PROMPTS),
        "status_text": "Equilibrio analítico perfecto. Mente despejada."
    }


# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "current_input" not in st.session_state:
    st.session_state.current_input = ""
if "target_lang" not in st.session_state:
    st.session_state.target_lang = "en"
if "history" not in st.session_state:
    st.session_state.history = []

# Default state before any input
default_mood = {
    "mood_id": "idle",
    "mood_name": "Modo Centinela",
    "emoji": "👁️",
    "marker": "idle",
    "color_theme": "#00e5ff",
    "bg_glow": "rgba(0, 229, 255, 0.15)",
    "action_title": "Esperando Transmisión...",
    "action_content": "Escribe tus pensamientos en el terminal. Detectaré tu espectro emocional y reaccionaré en tiempo real.",
    "status_text": "Sistemas activos. Radar neuronal en espera."
}

# -----------------------------------------------------------------------------
# GLOWING NOIR CSS & INTERACTIVE BACKGROUND
# -----------------------------------------------------------------------------
raw_lottie_json_str = json.dumps(lottie_data) if lottie_data else "null"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Syne:wght@400;600;800&family=JetBrains+Mono:wght@300;400;600&display=swap');

    /* Global Noir Base */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #05070c !important;
        color: #e0e6ed !important;
        font-family: 'Syne', sans-serif !important;
        overflow-x: hidden;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Subtle Scanline Overlay */
    [data-testid="stAppViewContainer"]::before {
        content: " ";
        position: fixed;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 26, 0) 50%, rgba(0, 0, 0, 0.25) 50%);
        background-size: 100% 4px;
