import os
import json
import copy
import random
from io import BytesIO
import streamlit as st
from streamlit_lottie import st_lottie
from textblob import TextBlob
from gtts import gTTS

# Expose st.lottie alias matching your course slide syntax
st.lottie = st_lottie

# Translation engine with robust fallback for Python 3.11
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


# -----------------------------------------------------------------------------
# 1. PAGE SETUP & GLOWING NOIR STYLING (Python 3.11 Safe)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NOIR.AI // Emotion Companion",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Raw string literal prevents any curly brace syntax errors in Python 3.11
NOIR_ATMOSPHERE_HTML = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=JetBrains+Mono:wght@300;400;600&family=Syne:wght@400;600;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #05070c !important;
    color: #e4edf8 !important;
    font-family: 'Syne', sans-serif !important;
    overflow-x: hidden;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* CRT Scanline effect */
[data-testid="stAppViewContainer"]::before {
    content: " ";
    position: fixed;
    top: 0; left: 0; bottom: 0; right: 0;
    background: linear-gradient(rgba(18, 16, 26, 0) 50%, rgba(0, 0, 0, 0.3) 50%);
    background-size: 100% 4px;
    z-index: 1;
    pointer-events: none;
    opacity: 0.5;
}

#noir-canvas-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 0;
    pointer-events: none;
}

.orbitron-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.6rem;
    font-weight: 900;
    letter-spacing: 2px;
    background: linear-gradient(135deg, #ffffff 10%, #64d2ff 60%, #0077ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

.mono-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    letter-spacing: 3px;
    color: #64d2ff;
    text-shadow: 0 0 10px rgba(100, 210, 255, 0.5);
    text-transform: uppercase;
}

.noir-card {
    background: rgba(11, 15, 25, 0.75);
    border: 1px solid rgba(100, 210, 255, 0.15);
    border-radius: 18px;
    padding: 24px;
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.85), inset 0 0 20px rgba(100, 210, 255, 0.03);
    margin-bottom: 20px;
    transition: transform 0.3s ease, border-color 0.3s ease;
}

.noir-card:hover {
    border-color: rgba(100, 210, 255, 0.35);
    transform: translateY(-2px);
}

.lottie-pedestal {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle at center, rgba(100, 210, 255, 0.06) 0%, rgba(5, 7, 12, 0) 70%);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 20px;
    padding: 16px;
    min-height: 400px;
}

.stTextInput input {
    background: rgba(13, 19, 33, 0.85) !important;
    border: 1px solid rgba(100, 210, 255, 0.25) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.05rem !important;
    padding: 14px 18px !important;
    box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.7) !important;
}

.stTextInput input:focus {
    border-color: #64d2ff !important;
    box-shadow: 0 0 20px rgba(100, 210, 255, 0.35) !important;
}
</style>

<canvas id="noir-canvas-bg"></canvas>

<script>
(function() {
    const canvas = document.getElementById('noir-canvas-bg');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w = canvas.width = window.innerWidth;
    let h = canvas.height = window.innerHeight;

    window.addEventListener('resize', () => {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    });

    const particles = [];
    const trail = [];

    window.addEventListener('mousemove', (e) => {
        for (let i = 0; i < 2; i++) {
            trail.push({
                x: e.clientX + (Math.random() - 0.5) * 6,
                y: e.clientY + (Math.random() - 0.5) * 6,
                size: Math.random() * 2.5 + 1,
                alpha: 0.9,
                decay: Math.random() * 0.025 + 0.015,
                vx: (Math.random() - 0.5) * 1.2,
                vy: (Math.random() - 0.5) * 1.2
            });
        }
    });

    for (let i = 0; i < 60; i++) {
        particles.push({
            x: Math.random() * w,
            y: Math.random() * h,
            r: Math.random() * 1.6 + 0.4,
            vx: (Math.random() - 0.5) * 0.25,
            vy: (Math.random() - 0.5) * 0.25,
            alpha: Math.random() * 0.5 + 0.2
        });
    }

    function animate() {
        ctx.clearRect(0, 0, w, h);

        // Ambient particles
        for (let p of particles) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(100, 210, 255, " + (p.alpha * 0.35) + ")";
            ctx.shadowBlur = 6;
            ctx.shadowColor = "#64d2ff";
            ctx.fill();
        }

        // Mouse trail
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
            ctx.fillStyle = "rgba(0, 240, 255, " + (t.alpha * 0.65) + ")";
            ctx.shadowBlur = 10;
            ctx.shadowColor = "#00f0ff";
            ctx.fill();
        }
        requestAnimationFrame(animate);
    }
    animate();
})();
</script>
"""

st.markdown(NOIR_ATMOSPHERE_HTML, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. LOTTIE LOADER & MARKER SLICER (Supports graficos.json & AI robo.json)
# -----------------------------------------------------------------------------
@st.cache_data
def load_lottie_source():
    """Detects and loads the Lottie animation file available in the directory."""
    candidates = ["graficos.json", "AI robo.json", "ai_robo.json", "animation.json"]
    for path in candidates:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as source:
                    return json.load(source)
            except Exception:
                pass

    # Generic search for any local Lottie JSON
    for fname in os.listdir("."):
        if fname.endswith(".json") and fname not in ["package.json", "tsconfig.json"]:
            try:
                with open(fname, "r", encoding="utf-8") as source:
                    data = json.load(source)
                    if isinstance(data, dict) and "layers" in data:
                        return data
            except Exception:
                continue
    return None


base_animation = load_lottie_source()


def get_mood_animation_slice(raw_anim, marker_name: str):
    """
    Slices the Lottie animation's in-point (ip) and out-point (op)
    so st.lottie loops the exact emotion segment without buttons.
    """
    if not raw_anim or not isinstance(raw_anim, dict):
        return None

    sliced = copy.deepcopy(raw_anim)
    total_frames = raw_anim.get("op", 0)

    # Frame slices defined in AI robo.json markers
    marker_map = {
        "idle": (0, 30),
        "yes": (31, 105),
        "no": (106, 180),
        "alert": (181, 270),
        "thinking": (271, 390),
        "jump": (391, 479),
    }

    if total_frames >= 400 and marker_name in marker_map:
        start_f, end_f = marker_map[marker_name]
        sliced["ip"] = start_f
        sliced["op"] = end_f

    return sliced


# -----------------------------------------------------------------------------
# 3. TRANSLATION & TTS UTILITIES
# -----------------------------------------------------------------------------
def translate_phrase(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    """Translates text with deep-translator, googletrans, or safe fallback."""
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


def synthesize_speech(text: str, lang: str = "es") -> bytes:
    """Generates an MP3 audio buffer using gTTS."""
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return b""


# -----------------------------------------------------------------------------
# 4. EMOTIONAL PROTOCOLS & ACTION RESPONSES
# -----------------------------------------------------------------------------
JOKES_SAD = [
    "—Papá, ¿qué se siente tener un hijo tan inteligente? —No sé hijo, pregúntale a tu abuelo.",
    "¿Qué le dice un bit a otro? —Nos vemos en el bus.",
    "¿Por qué los pájaros no usan WhatsApp? —Porque ya tienen Twitter.",
    "¿Cómo maldice un informático cuando se frustra? —¡Me cago en el bit que te parió!",
    "¿Qué hace una abeja en el gimnasio? —¡Zumba!",
    "Tranquilo/a: hasta el código más elegante tuvo errores antes de compilar con éxito.",
]

MOTIVATIONS_HAPPY = [
    "¡Tu energía está al máximo! Toma esa idea que posponías y ejecútala hoy mismo.",
    "¡Excelente momento! Cada decisión que tomes con esta confianza multiplicará tus resultados.",
    "¡Estás en racha! Aprovecha este impulso para derribar tus mayores desafíos de la semana.",
    "La pasión y el enfoque juntos son imparables. ¡Sigue acelerando!",
]

ADVICE_ANGER = [
    "Respira profundo: Inhala en 4 segundos... Mantén 4... Exhala lentamente en 6. Retoma el control.",
    "La ira es fuego que quema primero las manos de quien la sostiene. Observa con mente fría.",
    "Tómate dos minutos de pausa, bebe agua fresca y no tomes decisiones definitivas con la mente alterada.",
    "La verdadera fuerza radica en la serenidad frente a la tormenta.",
]

PROMPTS_NEUTRAL = [
    "Estado de equilibrio ideal. Es el mejor momento para analizar datos y metas sin sesgos.",
    "La neutralidad es la antesala de la creatividad objetiva.",
    "Mente despejada: buen instante para planificar tus próximos pasos con precisión táctica.",
]

ANGER_KEYWORDS = [
    "odio", "furia", "enojado", "enojada", "rabia", "molesto", "molesta", "ira",
    "maldito", "maldita", "angry", "furious", "hate", "mad", "pissed", "rage"
]

EXCITED_KEYWORDS = [
    "increíble", "asombroso", "genial", "excelente", "vamos", "fuego", "logro",
    "victoria", "campeón", "awesome", "amazing", "pumped", "hyped", "thrilled"
]


def evaluate_sentiment(text_es: str, polarity: float, subjectivity: float):
    """Diagnoses mood, chooses Lottie animation marker and action protocol."""
    lower_text = text_es.lower()

    # Anger / High Tension
    if any(k in lower_text for k in ANGER_KEYWORDS) or (polarity < -0.3 and subjectivity > 0.6):
        return {
            "mood_name": "Tensión / Alerta Emocional",
            "emoji": "⚡",
            "marker": "alert",
            "color": "#ff375f",
            "protocol_name": "Protocolo de Desescalada & Calma",
            "action": random.choice(ADVICE_ANGER),
            "status": "Resonancia alterada detectada. Ejecutando modulación de estrés.",
        }

    # High Excitement
    if any(k in lower_text for k in EXCITED_KEYWORDS) or (polarity >= 0.5):
        return {
            "mood_name": "Euforia / Alta Vibración",
            "emoji": "🚀",
            "marker": "jump",
            "color": "#30d158",
            "protocol_name": "Protocolo Catalizador de Acción",
            "action": random.choice(MOTIVATIONS_HAPPY),
            "status": "Pico de energía detectado. Canalizando impulso creativo.",
        }

    # Standard Positive
    if polarity > 0.05:
        return {
            "mood_name": "Sentimiento Positivo",
            "emoji": "😊",
            "marker": "yes",
            "color": "#64d2ff",
            "protocol_name": "Protocolo de Motivación",
            "action": random.choice(MOTIVATIONS_HAPPY),
            "status": "Armonía detectada. El compañero asiente y refuerza tu optimismo.",
        }

    # Sad / Down
    if polarity < -0.05:
        return {
            "mood_name": "Sentimiento Negativo / Melancolía",
            "emoji": "😔",
            "marker": "no",
            "color": "#bf5af2",
            "protocol_name": "Protocolo Reanimador // Chiste",
            "action": random.choice(JOKES_SAD),
            "status": "Frecuencia baja detectada. Desplegando dosis de humor y calidez.",
        }

    # Neutral
    return {
        "mood_name": "Sentimiento Neutral / Contemplativo",
        "emoji": "😐",
        "marker": "thinking",
        "color": "#00f0ff",
        "protocol_name": "Protocolo de Reflexión",
        "action": random.choice(PROMPTS_NEUTRAL),
        "status": "Equilibrio analítico. El compañero reflexiona sobre tu mensaje.",
    }


# -----------------------------------------------------------------------------
# 5. USER INTERFACE (No buttons required)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <div style="text-align: center; margin-top: 10px; margin-bottom: 25px;">
        <span class="mono-subtitle">// SISTEMA INTERACTIVO DE ANÁLISIS DE SENTIMIENTO //</span>
        <div class="orbitron-title">COMPAÑERO NEURONAL</div>
        <p style="color: #7b93af; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;">
            Escribe en el campo de texto y pulsa Enter. El robot Lottie responderá automáticamente según tu emoción.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Input Controls
col_text, col_lang = st.columns([3.2, 1], gap="medium")

with col_text:
    user_input = st.text_input(
        label="Escribe tu frase aquí:",
        placeholder="Ej: Hoy ha sido un día difícil pero sigo adelante... / ¡Aprobé mi examen con éxito!",
        key="phrase_input",
    )

with col_lang:
    target_lang = st.selectbox(
        label="Traducir resultado a:",
        options=["en", "es", "fr", "ja", "de", "it", "pt"],
        format_func=lambda code: {
            "en": "🇬🇧 Inglés (EN)",
            "es": "🇪🇸 Español (ES)",
            "fr": "🇫🇷 Francés (FR)",
            "ja": "🇯🇵 Japonés (JA)",
            "de": "🇩🇪 Alemán (DE)",
            "it": "🇮🇹 Italiano (IT)",
            "pt": "🇵🇹 Portugués (PT)",
        }.get(code, code),
        index=0,
    )

# Real-Time Sentiment & Mood Computation
if user_input and user_input.strip():
    # 1. Translate to English for TextBlob accuracy
    english_translation = translate_phrase(user_input, source_lang="auto", target_lang="en")
    blob = TextBlob(english_translation)
    polarity_val = round(blob.sentiment.polarity, 2)
    subjectivity_val = round(blob.sentiment.subjectivity, 2)

    # 2. Translate user phrase into selected target language
    multilingual_text = translate_phrase(user_input, source_lang="auto", target_lang=target_lang)

    # 3. Determine mood & reaction
    mood_result = evaluate_sentiment(user_input, polarity_val, subjectivity_val)
else:
    polarity_val = 0.0
    subjectivity_val = 0.0
    english_translation = ""
    multilingual_text = ""
    mood_result = {
        "mood_name": "Esperando Entrada",
        "emoji": "👁️",
        "marker": "idle",
        "color": "#64d2ff",
        "protocol_name": "Modo Centinela",
        "action": "Escribe una frase en el terminal para activar los sensores del compañero.",
        "status": "Compañero en espera pasiva. Radar de sentimientos activo.",
    }

# Prepare sliced animation
active_lottie = get_mood_animation_slice(base_animation, mood_result["marker"])


# -----------------------------------------------------------------------------
# 6. DUAL PANEL: LOTTIE COMPANION & TELEMETRY MONITOR
# -----------------------------------------------------------------------------
col_visual, col_info = st.columns([1.1, 1], gap="large")

with col_visual:
    st.markdown('<div class="noir-card lottie-pedestal">', unsafe_allow_html=True)

    if active_lottie:
        # Uses st_lottie / st.lottie as demonstrated in your course slides
        st.lottie(
            active_lottie,
            width=350,
            key=f"lottie_player_{mood_result['marker']}",
        )
    else:
        st.warning("⚠️ No se encontró 'graficos.json' o 'AI robo.json' en el directorio.")

    st.markdown(
        f"""
        <div style="font-family: 'Orbitron'; font-size: 0.8rem; letter-spacing: 2px; color: {mood_result['color']}; margin-top: 8px;">
            ESTADO ACTIVO: {mood_result['marker'].upper()}
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with col_info:
    st.markdown(
        f"""
        <div class="noir-card" style="border-left: 4px solid {mood_result['color']};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: {mood_result['color']}; font-family: 'Orbitron'; font-size: 0.85rem; font-weight: 700;">
                    {mood_result['emoji']} TELEMETRÍA
                </span>
                <span style="font-family: 'JetBrains Mono'; font-size: 0.85rem; background: rgba(0,0,0,0.4); padding: 4px 10px; border-radius: 12px; border: 1px solid {mood_result['color']}; color: {mood_result['color']};">
                    POLARIDAD: {polarity_val}
                </span>
                <span style="font-family: 'JetBrains Mono'; font-size: 0.85rem; background: rgba(0,0,0,0.4); padding: 4px 10px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);">
                    SUBJETIVIDAD: {subjectivity_val}
                </span>
            </div>

            <h2 style="font-size: 1.7rem; margin: 4px 0 8px 0; color: #ffffff;">
                {mood_result['mood_name']}
            </h2>
            <p style="color: #8fa6c2; font-family: 'JetBrains Mono'; font-size: 0.85rem; margin-bottom: 16px;">
                {mood_result['status']}
            </p>

            <div style="background: rgba(0,0,0,0.45); border-radius: 12px; padding: 16px; border: 1px dashed rgba(255,255,255,0.12); margin-bottom: 16px;">
                <div style="font-family: 'Orbitron'; font-size: 0.8rem; color: {mood_result['color']}; font-weight: 700; margin-bottom: 6px;">
                    ⚡ {mood_result['protocol_name']}
                </div>
                <div style="font-size: 1rem; line-height: 1.5; color: #f5f8fc;">
                    "{mood_result['action']}"
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Voice TTS Player for companion response
    if user_input and user_input.strip():
        spoken_text = f"{mood_result['mood_name']}. {mood_result['action']}"
        audio_bytes = synthesize_speech(spoken_text, lang="es")
        if audio_bytes:
            st.caption("🔊 Voz Sintetizada del Compañero:")
            st.audio(audio_bytes, format="audio/mp3")

    # Multilingual Translation Display
    if multilingual_text:
        st.markdown(
            f"""
            <div style="background: rgba(100, 210, 255, 0.05); border-radius: 12px; padding: 12px 16px; border: 1px solid rgba(100, 210, 255, 0.2); margin-top: 10px;">
                <div style="font-family: 'JetBrains Mono'; font-size: 0.75rem; color: #64d2ff; letter-spacing: 1px;">
                    TRADUCCIÓN EN TIEMPO REAL ({target_lang.upper()}):
                </div>
                <div style="font-family: 'JetBrains Mono'; font-size: 0.95rem; color: #ffffff; margin-top: 4px;">
                    "{multilingual_text}"
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 7. SIDEBAR: POLARITY & SUBJECTIVITY REFERENCE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 📊 Polaridad y Subjetividad")
    st.info(
        """
        **Polaridad (-1 a 1):**
        Indica si el sentimiento expresado en el texto es positivo, negativo o neutral.
        - `> 0`: Sentimiento Positivo 😊 (Activa protocolo de motivación)
        - `< 0`: Sentimiento Negativo 😔 (Activa protocolo de humor/chistes)
        - `~ 0`: Sentimiento Neutral 😐 (Activa protocolo de reflexión)
        
        **Subjetividad (0 a 1):**
        Mide cuánto del contenido es subjetivo (opiniones, emociones, creencias) frente a objetivo (hechos).
        """
    )
    st.markdown("---")
    st.caption("🤖 NOIR.AI Engine // Python 3.11 // Powered by TextBlob & Streamlit-Lottie")
