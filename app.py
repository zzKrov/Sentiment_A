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

st.lottie = st_lottie

# -----------------------------------------------------------------------------
# MOTORES DE VOZ NEURAL Y TRADUCCIÓN RESILIENTE
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

    try:
        tts = gTTS(text=text, lang="es", tld="es", slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return b""


def render_clean_html(html_str: str):
    clean = "".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


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
# CARGA Y FILTRADO DEL LOTTIE
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
        "AI robo.json", "graficos.json", "ai robo.json",
        "AI_robo.json", "ai_robo.json", "robot.json",
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
    "¿Cómo se despiden los informáticos? —Ácido un placer.",
    "¿Qué hace una abeja en el gimnasio? —¡Zumba!",
    "Recuerda: incluso el código mejor optimizado falló muchas veces antes de funcionar.",
]

MOTIVACIONES = [
    "¡Qué alegría leerte con tanto entusiasmo! Aprovecha este buen momento para avanzar en tus proyectos y celebrar los logros.",
    "¡Esa es una excelente actitud! Con esa energía positiva se resuelven mejor los retos. ¡Sigue así!",
    "¡Se nota que las cosas van por buen camino! Mantén ese optimismo y comparte esa buena disposición con tu equipo.",
]

CONSEJOS_CALMA = [
    "Es completamente natural sentirse con tensión cuando las tareas se acumulan. Haz una pausa breve, respira hondo y retoma con calma.",
    "Comprendo la incomodidad de la situación. Date unos minutos para despejar la mente; cuidar tu bienestar siempre es prioritario.",
    "A veces la jornada resulta compleja. Suelta la tensión un instante y organiza las prioridades paso a paso.",
]

CONVERSACION_NEUTRAL = [
    "Te escucho atentamente. Los momentos de calma son excelentes para reflexionar, planificar o simplemente descansar.",
    "Comprendo lo que planteas. Tómate el tiempo necesario para evaluar las opciones con serenidad.",
]

JUMP_WORDS = ["gané", "logré", "triunfo", "increíble", "asombroso", "celebrar", "fiesta", "campeón", "victoria", "genial", "aprobé"]
YES_WORDS = ["bien", "feliz", "contento", "me gusta", "alegre", "gracias", "bueno", "excelente", "agradecido", "positivo"]
ALERT_WORDS = ["cuidado", "alerta", "estrés", "ansiedad", "nervioso", "preocupado", "urgente", "peligro", "tensión", "miedo", "ojo"]
NO_WORDS = ["no", "odio", "rabia", "molesto", "enojado", "pésimo", "terrible", "desastre", "triste", "mal", "asco", "horrible"]
THINK_WORDS = ["pensando", "quizás", "tal vez", "duda", "curioso", "analizando", "pregunto", "tranquilo", "calma", "depende"]


def analyze_conversation(user_text: str, polarity: float, subjectivity: float):
    lower_text = user_text.lower()

    if any(k in lower_text for k in JUMP_WORDS) or polarity >= 0.55:
        return {
            "title": "¡Excelente logro, me alegro mucho!",
            "feeling": "Celebración y Entusiasmo",
            "emoji": "🚀",
            "marker": "jump",
            "accent_color": "#00f0ff",
            "is_gradient": True,
            "glow": "rgba(255, 0, 127, 0.55)",
            "message": random.choice(MOTIVACIONES),
        }

    if any(k in lower_text for k in YES_WORDS) or polarity > 0.05:
        return {
            "title": "¡Qué buena noticia, todo avanza positivamente!",
            "feeling": "Optimista y Satisfecho",
            "emoji": "😊",
            "marker": "yes",
            "accent_color": "#00ff88",
            "is_gradient": False,
            "glow": "rgba(0, 255, 136, 0.5)",
            "message": random.choice(MOTIVACIONES),
        }

    if any(k in lower_text for k in ALERT_WORDS) or (subjectivity > 0.65 and polarity < 0.1):
        return {
            "title": "Momento de pausa: tómate un respiro...",
            "feeling": "Precaución y Tensión",
            "emoji": "⚠️",
            "marker": "alert",
            "accent_color": "#ffd600",
            "is_gradient": False,
            "glow": "rgba(255, 214, 0, 0.5)",
            "message": random.choice(CONSEJOS_CALMA),
        }

    if any(k in lower_text for k in NO_WORDS) or polarity < -0.05:
        return {
            "title": "Comprendo el malestar... no te desanimes",
            "feeling": "Descontento o Desánimo",
            "emoji": "🛑",
            "marker": "no",
            "accent_color": "#ff3344",
            "is_gradient": False,
            "glow": "rgba(255, 51, 68, 0.5)",
            "message": f"Es comprensible sentir frustración ante momentos difíciles. Para distenderte un poco, aquí tienes un chiste:\n\n{random.choice(CHISTES)}",
        }

    return {
        "title": "Te escucho con atención, analicemos la situación...",
        "feeling": "Reflexivo y Neutral",
        "emoji": "🔮",
        "marker": "thinking",
        "accent_color": "#bf5af2",
        "is_gradient": False,
        "glow": "rgba(191, 90, 242, 0.5)",
        "message": random.choice(CONVERSACION_NEUTRAL),
    }


# -----------------------------------------------------------------------------
# ESTADO DE SESIÓN
# -----------------------------------------------------------------------------
if "phrase_input" not in st.session_state:
    st.session_state.phrase_input = ""

def set_quick_phrase(phrase: str):
    st.session_state.phrase_input = phrase

# -----------------------------------------------------------------------------
# ENCABEZADO Y ACCESOS RÁPIDOS
# -----------------------------------------------------------------------------
render_clean_html(
    """
    <div style="text-align: center; margin-top: 5px; margin-bottom: 14px;">
        <div style="font-family:'JetBrains Mono', monospace; font-size:0.75rem; letter-spacing:2px; color:#64d2ff; text-transform:uppercase; margin-bottom:4px;">
            Krov Industries · Interacción Afectiva
        </div>
        <div class="title-glow">Compañero de Conversación y Ánimo</div>
        <p style="color: #8da4be; font-size: 0.95rem; margin-top: 2px;">
            Escribe cómo te sientes hoy para recibir una respuesta orientativa y contextualizada.
        </p>
    </div>
    """
)

render_clean_html(
    """
    <div style="text-align: center; margin-bottom: 10px;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64d2ff; letter-spacing: 1.5px; text-transform: uppercase;">
            Selección rápida de estados:
        </span>
    </div>
    """
)

chip_cols = st.columns(5)
with chip_cols[0]:
    if st.button("🚀 ¡Celebrar logro!", use_container_width=True):
        set_quick_phrase("¡Gané el concurso y alcanzamos un resultado excelente!")
        st.rerun()

with chip_cols[1]:
    if st.button("😊 Todo en orden", use_container_width=True):
        set_quick_phrase("Todo está marchando muy bien hoy.")
        st.rerun()

with chip_cols[2]:
    if st.button("⚠️ Día estresante", use_container_width=True):
        set_quick_phrase("Siento mucha tensión y preocupación por los plazos de entrega.")
        st.rerun()

with chip_cols[3]:
    if st.button("🛑 Mala jornada", use_container_width=True):
        set_quick_phrase("Hoy todo salió al revés y siento bastante enojo.")
        st.rerun()

with chip_cols[4]:
    if st.button("🔮 Pensativo", use_container_width=True):
        set_quick_phrase("Estoy pensando y evaluando qué camino tomar.")
        st.rerun()

st.write("")

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
            "en": "Inglés (EN)", "es": "Español (ES)", "fr": "Francés (FR)",
            "ja": "Japonés (JA)", "de": "Alemán (DE)", "it": "Italiano (IT)", "pt": "Portugués (PT)",
        }.get(c, c),
        index=0,
    )

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
        "title": "¡Hola! ¿Cómo te encuentras en este momento?",
        "feeling": "En espera de conversación",
        "emoji": "👋",
        "marker": "idle",
        "accent_color": "#00f0ff",
        "is_gradient": False,
        "glow": "rgba(0, 240, 255, 0.45)",
        "message": "Cuéntame cómo estuvo tu jornada o qué estás experimentando. Aquí estaré para acompañarte.",
    }

active_lottie = get_mood_slice(base_animation, response["marker"])

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
# ESTILOS DINÁMICOS
# -----------------------------------------------------------------------------
NOIR_FULL_FX = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --mood-color: __COLOR__;
    --mood-glow: __GLOW__;
}

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

.title-glow {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    background: linear-gradient(135deg, #ffffff 10%, var(--mood-color) 60%, #ffffff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 35px var(--mood-glow);
    margin-bottom: 4px;
    transition: all 0.5s ease;
}

.card-noir-dialogue {
    position: relative;
    border-radius: 20px;
    padding: 24px;
    backdrop-filter: blur(20px);
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.8), 0 0 30px var(--mood-glow);
    transition: all 0.4s ease;
    __BORDER_CSS__
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    position: relative !important;
    border-radius: 20px !important;
    padding: 20px 20px 16px 20px !important;
    backdrop-filter: blur(20px) !important;
    box-shadow: 0 15px 45px rgba(0, 0, 0, 0.8), 0 0 35px var(--mood-glow) !important;
    __BORDER_CSS__
}

div[data-testid="stLottie"], iframe[title="streamlit_lottie.st_lottie"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 0 auto !important;
    filter: drop-shadow(0 0 28px var(--mood-glow));
    transition: filter 0.5s ease;
}

.stButton > button {
    background: rgba(13, 19, 33, 0.85) !important;
    border: 1px solid rgba(100, 210, 255, 0.25) !important;
    border-radius: 24px !important;
    color: #e4edf8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    padding: 8px 14px !important;
    transition: all 0.25s ease !important;
}

.stButton > button:hover {
    border-color: var(--mood-color) !important;
    box-shadow: 0 0 20px var(--mood-glow) !important;
    color: #ffffff !important;
}

.holo-base {
    position: relative;
    width: 100%;
    height: 38px;
    margin-top: -24px;
    margin-bottom: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
}

.holo-ring-outer {
    position: absolute;
    width: 200px;
    height: 42px;
    border-radius: 50%;
    border: 2px dashed var(--mood-color);
    box-shadow: 0 0 18px var(--mood-color);
    transform: rotateX(75deg);
    opacity: 0.85;
}

.gauge-track {
    position: relative;
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    margin: 8px 0;
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
    transition: left 0.4s ease;
}
</style>
""".replace("__COLOR__", response["accent_color"]).replace("__GLOW__", response["glow"]).replace("__BORDER_CSS__", border_css)

render_clean_html(NOIR_FULL_FX)

col_dialogo, col_robo = st.columns([1.25, 1], gap="large")

with col_dialogo:
    render_clean_html(
        f"""
        <div class="card-noir-dialogue">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="color: {response['accent_color']}; font-family: 'Orbitron'; font-size: 0.85rem; font-weight: 700; letter-spacing: 1.2px;">
                    {response['emoji']} RESPUESTA DEL ASISTENTE
                </span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: rgba(0,0,0,0.4); padding: 4px 10px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.1); color: #c4d7ec;">
                    Subjetividad: {int(subjectivity_val * 100)}%
                </span>
            </div>

            <h2 style="font-size: 1.5rem; font-weight: 700; margin: 0 0 12px 0; color: #ffffff;">
                {response['title']}
            </h2>

            <div style="font-size: 1.05rem; line-height: 1.6; color: #edf4fc; background: rgba(0,0,0,0.35); padding: 16px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px;">
                {response['message'].replace(chr(10), '<br>')}
            </div>
        </div>
        """
    )

    if user_phrase and user_phrase.strip():
        selected_male_voice = st.session_state.get("preferred_voice", "es-ES-AlvaroNeural")
        spoken_text = f"{response['title']}. {response['message']}"
        voice_audio = get_speech_audio(spoken_text, voice_name=selected_male_voice)

        if voice_audio:
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

    if translated_display:
        render_clean_html(
            f"""
            <div style="background: rgba(100, 210, 255, 0.05); border-radius: 12px; padding: 12px 16px; border: 1.5px solid {response['accent_color']}; margin-top: 10px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: {response['accent_color']}; letter-spacing: 1.2px;">
                    TRADUCCIÓN ({selected_lang.upper()}):
                </div>
                <div style="font-size: 0.95rem; color: #ffffff; margin-top: 3px;">
                    "{translated_display}"
                </div>
            </div>
            """
        )

with col_robo:
    with st.container(border=True):
        render_clean_html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; width: 100%;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: {response['accent_color']}; letter-spacing: 1.5px;">
                    ● ESTADO ACTIVO
                </span>
                <span style="font-size: 0.85rem; font-weight: 700; color: #ffffff;">
                    {response['emoji']} {response['feeling']}
                </span>
            </div>
            """
        )

        if active_lottie:
            st.lottie(
                active_lottie,
                width=270,
                height=270,
                key=f"hologram_robot_{response['marker']}",
            )
        else:
            st.info("Cargando componente de animación...")

        render_clean_html(
            """
            <div class="holo-base">
                <div class="holo-ring-outer"></div>
            </div>
            """
        )

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

with st.sidebar:
    st.markdown("### Configuración de Voz")
    voice_options = {
        "es-ES-AlvaroNeural": "Voz Masculina (Álvaro - España)",
        "es-MX-JorgeNeural": "Voz Masculina (Jorge - México)",
        "es-CO-GonzaloNeural": "Voz Masculina (Gonzalo - Colombia)",
        "es-AR-TomasNeural": "Voz Masculina (Tomás - Argentina)",
    }
    st.selectbox(
        label="Seleccionar modulación de voz:",
        options=list(voice_options.keys()),
        format_func=lambda v: voice_options[v],
        key="preferred_voice",
    )
