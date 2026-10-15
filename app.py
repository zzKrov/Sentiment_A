import os
import json
import copy
import random
import asyncio
import base64
import urllib.request
import urllib.parse
from io import BytesIO
import streamlit as st
from streamlit_lottie import st_lottie
from textblob import TextBlob
from gtts import gTTS

st.lottie = st_lottie

# -----------------------------------------------------------------------------
# TRADUCCIÓN RESILIENTE DIRECTA Y DE RESPALDO
# -----------------------------------------------------------------------------
def translate_phrase(text: str, source_lang: str = "auto", target_lang: str = "en") -> str:
    if not text or not text.strip() or source_lang == target_lang:
        return text

    # Intento 1: API Directa de Google (Garantiza funcionamiento sin fallos de librería)
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
            return "".join(part[0] for part in data[0] if part[0])
    except Exception:
        pass

    # Intento 2: deep_translator si está disponible
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source=source_lang, target=target_lang).translate(text)
    except Exception:
        pass

    # Intento 3: googletrans si está disponible
    try:
        from googletrans import Translator as GTrans
        return GTrans().translate(text, src=source_lang, dest=target_lang).text
    except Exception:
        pass

    return text


def get_speech_audio(text: str) -> bytes:
    if not text or not text.strip():
        return b""
    try:
        tts = gTTS(text=text, lang="es", tld="com.mx", slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return b""

# -----------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Compañero Emocional // Krov Industries",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# CARGA Y CORTE EXACTO DEL LOTTIE
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_lottie():
    search_dirs = [os.getcwd(), ".", os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."]
    filenames = ["AI robo.json", "graficos.json", "ai robo.json", "robot.json"]
    for sdir in search_dirs:
        for fname in filenames:
            p = os.path.join(sdir, fname)
            if os.path.isfile(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            clean = copy.deepcopy(data)
                            clean["layers"] = [l for l in clean.get("layers", []) if l.get("ind", 99) > 10]
                            return clean
                except Exception:
                    pass
    return None

base_animation = load_and_clean_lottie()

def get_mood_slice(anim_data, marker: str):
    if not anim_data:
        return None
    sliced = copy.deepcopy(anim_data)
    marker_ranges = {
        "idle": (0, 30),
        "yes": (31, 105),
        "no": (106, 180),
        "alert": (181, 270),
        "thinking": (271, 390),
        "jump": (391, 479),
    }
    if marker in marker_ranges and anim_data.get("op", 0) >= 400:
        s, e = marker_ranges[marker]
        sliced["ip"] = s
        sliced["op"] = e
    return sliced

# -----------------------------------------------------------------------------
# LÓGICA DE CONVERSACIÓN RIGUROSAMENTE DIFERENCIADA
# -----------------------------------------------------------------------------
CHISTES = [
    "¿Qué le dice un bit a otro? —Nos vemos en el bus.",
    "¿Por qué los pájaros no usan WhatsApp? —Porque ya tienen Twitter.",
    "¿Cómo se despiden los químicos? —Ácido un placer.",
    "¿Qué hace una abeja en el gimnasio? —¡Zumba!",
    "Recuerda: incluso los mejores sistemas requieren un reinicio de vez en cuando.",
]

def analyze_conversation(user_text: str):
    lower = user_text.lower()
    en_txt = translate_phrase(user_text, source_lang="auto", target_lang="en")
    blob = TextBlob(en_txt)
    pol = round(blob.sentiment.polarity, 2)
    subj = round(blob.sentiment.subjectivity, 2)

    # 1. CELEBRACIÓN / TRIUNFO (JUMP)
    if any(k in lower for k in ["gané", "logré", "triunfo", "increíble", "celebrar", "victoria", "genial"]) or pol >= 0.55:
        return {
            "title": "¡Felicitaciones por ese gran logro!",
            "feeling": "Celebración y Victoria",
            "emoji": "🚀",
            "marker": "jump",
            "accent_color": "#00f0ff",
            "message": "Alcanzar una meta destacada merece celebrarse. Aprovecha este impulso de energía positiva para consolidar lo aprendido y disfrutar del éxito.",
            "polarity": pol, "subjectivity": subj
        }

    # 2. EN ORDEN / POSITIVO (YES)
    if any(k in lower for k in ["bien", "feliz", "contento", "bueno", "excelente", "orden", "tranquilo"]) or pol > 0.08:
        return {
            "title": "¡Me da gusto saber que todo marcha bien!",
            "feeling": "Optimismo y Satisfacción",
            "emoji": "😊",
            "marker": "yes",
            "accent_color": "#00ff88",
            "message": "La estabilidad y el buen ánimo son ideales para progresar de forma constante. Continúa con esa buena disposición a lo largo de tu jornada.",
            "polarity": pol, "subjectivity": subj
        }

    # 3. DÍA ESTRESANTE (ALERT) -> Manejo de ansiedad, pausas y carga laboral
    if any(k in lower for k in ["estrés", "estresante", "ansiedad", "nervioso", "preocupado", "tensión", "presión", "urgente"]):
        return {
            "title": "Momento de bajar el ritmo y priorizar...",
            "feeling": "Tensión y Sobrecarga",
            "emoji": "⚠️",
            "marker": "alert",
            "accent_color": "#ffd600",
            "message": "Cuando la presión laboral o los plazos se acumulan, el estrés nubla la toma de decisiones. Haz una pausa de cinco minutos, respira hondo y desglosa las tareas pendientes una a la vez.",
            "polarity": pol, "subjectivity": subj
        }

    # 4. MALA JORNADA (NO) -> Empatía ante reveses, desánimo y humor para distender
    if any(k in lower for k in ["mala jornada", "pésimo", "desastre", "mal día", "frustrado", "enojo", "triste", "horrible"]) or pol < -0.10:
        return {
            "title": "Lamento que las cosas hayan salido mal hoy...",
            "feeling": "Descontento y Desahogo",
            "emoji": "🛑",
            "marker": "no",
            "accent_color": "#ff3344",
            "message": f"Hay días difíciles donde los imprevistos golpean. No te culpes de más; descansa y recuerda que mañana es una nueva oportunidad. Para sacarte una sonrisa:\n\n{random.choice(CHISTES)}",
            "polarity": pol, "subjectivity": subj
        }

    # 5. PENSATIVO (THINKING) -> Reflexión estratégica, evaluación de opciones y calma
    return {
        "title": "Analicemos las variables con perspectiva...",
        "feeling": "Reflexivo y Analítico",
        "emoji": "🔮",
        "marker": "thinking",
        "accent_color": "#bf5af2",
        "message": "Estar en una encrucijada requiere mente fría. Sopesa los pros y contras de cada alternativa, evalúa las consecuencias a mediano plazo y tómate el tiempo necesario antes de decidir.",
        "polarity": pol, "subjectivity": subj
    }

# ---------------------------------------------------------
# ESTILOS VISUALES Y PEDESTAL HOLOGRÁFICO CENTRADO
# ---------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #05070c !important;
    color: #e6edf5 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

[data-testid="stHeader"] { background: transparent !important; }

.brand-signature {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    color: #38bdf8;
    text-transform: uppercase;
}

.holo-stage {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 12px;
    background: rgba(13, 16, 26, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}

.holo-pedestal {
    position: relative;
    width: 220px;
    height: 45px;
    margin-top: -20px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.holo-ring-outer {
    position: absolute;
    width: 210px;
    height: 40px;
    border-radius: 50%;
    border: 2px dashed #00f0ff;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.6);
    transform: rotateX(72deg);
    animation: spinHolo 8s linear infinite;
}

@keyframes spinHolo {
    0% { transform: rotateX(72deg) rotateZ(0deg); }
    100% { transform: rotateX(72deg) rotateZ(360deg); }
}

.dialogue-card {
    background: rgba(13, 16, 26, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-left: 4px solid #00f0ff;
    border-radius: 10px;
    padding: 18px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-signature">Krov Industries · Asistencia Empática</div>', unsafe_allow_html=True)
st.markdown("<h2 style='text-align:center; color:#ffffff; margin:2px 0 12px 0;'>Compañero de Conversación</h2>", unsafe_allow_html=True)

# ---------------------------------------------------------
# BOTONES RÁPIDOS
# ---------------------------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
user_phrase = ""

if "active_mood_text" not in st.session_state:
    st.session_state["active_mood_text"] = "Hola, ¿cómo estás hoy?"

with c1:
    if st.button("🚀 Celebrar logro", use_container_width=True):
        st.session_state["active_mood_text"] = "¡Gané el concurso y alcanzamos un resultado excelente!"
        st.rerun()
with c2:
    if st.button("😊 Todo en orden", use_container_width=True):
        st.session_state["active_mood_text"] = "Todo está marchando muy bien y con tranquilidad hoy."
        st.rerun()
with c3:
    if st.button("⚠️ Día estresante", use_container_width=True):
        st.session_state["active_mood_text"] = "Tengo mucha presión y estrés por la cantidad de trabajo acumulado."
        st.rerun()
with c4:
    if st.button("🛑 Mala jornada", use_container_width=True):
        st.session_state["active_mood_text"] = "Hoy ha sido un pésimo día, las cosas salieron mal y me siento frustrado."
        st.rerun()
with c5:
    if st.button("🔮 Pensativo", use_container_width=True):
        st.session_state["active_mood_text"] = "Estoy reflexionando y analizando con calma cuál es la mejor decisión que debo tomar."
        st.rerun()

col_txt, col_lang = st.columns([3, 1], gap="medium")
with col_txt:
    user_phrase = st.text_input(
        "¿Qué estás experimentando?",
        value=st.session_state.get("active_mood_text", ""),
        placeholder="Escribe lo que sientes..."
    )
with col_lang:
    target_lang = st.selectbox(
        "Traducir respuesta a:",
        options=["en", "es", "fr", "ja", "de", "it", "pt"],
        format_func=lambda c: {"en":"Inglés (EN)", "es":"Español (ES)", "fr":"Francés (FR)", "ja":"Japonés (JA)", "de":"Alemán (DE)", "it":"Italiano (IT)", "pt":"Portugués (PT)"}.get(c, c),
        index=0
    )

res = analyze_conversation(user_phrase)
active_lottie = get_mood_slice(base_animation, res["marker"])

col_diag, col_anim = st.columns([1.2, 1], gap="large")

with col_diag:
    st.markdown(
        f"""
        <div class="dialogue-card" style="border-left-color: {res['accent_color']};">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-family:'JetBrains Mono'; font-size:0.75rem; color:{res['accent_color']};">ESTADO: {res['feeling'].upper()}</span>
                <span style="font-family:'JetBrains Mono'; font-size:0.72rem; color:#94a3b8;">SUBJETIVIDAD: {int(res['subjectivity']*100)}%</span>
            </div>
            <h3 style="margin:0 0 8px 0; color:#ffffff;">{res['emoji']} {res['title']}</h3>
            <div style="font-size:1rem; line-height:1.6; color:#e2e8f0;">{res['message'].replace(chr(10), '<br>')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    audio_bytes = get_speech_audio(f"{res['title']} {res['message']}")
    if audio_bytes:
        st.write("")
        st.audio(audio_bytes, format="audio/mp3")

    if target_lang != "es":
        tr_text = translate_phrase(res["message"], source_lang="es", target_lang=target_lang)
        st.markdown(
            f"""
            <div style="background:rgba(56, 189, 248, 0.08); border-left:3px solid #38bdf8; border-radius:6px; padding:12px; margin-top:10px;">
                <div style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#38bdf8;">TRADUCCIÓN ({target_lang.upper()}):</div>
                <div style="font-size:0.92rem; color:#f1f5f9; margin-top:2px;">"{tr_text}"</div>
            </div>
            """,
            unsafe_allow_html=True
        )

with col_anim:
    st.markdown('<div class="holo-stage">', unsafe_allow_html=True)
    if active_lottie:
        st.lottie(active_lottie, width=260, height=260, key=f"anim_{res['marker']}")
    else:
        st.info("Avatar animado en espera...")
    st.markdown(
        f"""
        <div class="holo-pedestal">
            <div class="holo-ring-outer" style="border-color:{res['accent_color']}; box-shadow:0 0 15px {res['accent_color']};"></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
