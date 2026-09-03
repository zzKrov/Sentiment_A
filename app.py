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

# Compatibilidad con sintaxis st.lottie
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

    # Voz masculina neural
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
    """Elimina sangrías para que Markdown no interprete HTML como bloques de código."""
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

    if not loaded_json:
        return None

    # Desactivar capas de botones (capas 1 a 10)
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
# TRADUCCIÓN Y REGLAS DE SENTIMIENTO
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

ANGER_WORDS = [
    "odio", "furia", "enojado", "enojada", "rabia", "molesto", "molesta", "ira",
    "maldito", "maldita", "angry", "furious", "hate", "mad", "pissed", "rage"
]

EXCITED_WORDS = [
    "increíble", "asombroso", "genial", "excelente", "vamos", "fuego", "logro",
    "victoria", "campeón", "awesome", "amazing", "pumped", "hyped"
]


def analyze_conversation(user_text: str, polarity: float, subjectivity: float):
    lower_text = user_text.lower()

    if any(k in lower_text for k in ANGER_WORDS) or (polarity < -0.3 and subjectivity > 0.6):
        return {
            "title": "Respira hondo, aquí estoy contigo...",
            "feeling": "Noté algo de frustración",
            "emoji": "🌿",
            "marker": "alert",
            "color": "#ff3366",
            "glow": "rgba(255, 51, 102, 0.4)",
            "message": random.choice(CONSEJOS_CALMA),
        }

    if any(k in lower_text for k in EXCITED_WORDS) or (polarity >= 0.5):
        return {
            "title": "¡Qué gran noticia, me alegro mucho!",
            "feeling": "¡Mucha alegría y emoción!",
            "emoji": "🎉",
            "marker": "jump",
            "color": "#00ff88",
            "glow": "rgba(0, 255, 136, 0.4)",
            "message": random.choice(MOTIVACIONES),
        }

    if polarity > 0.05:
        return {
            "title": "¡Qué gusto leer esto!",
            "feeling": "Buena vibra detectada",
            "emoji": "😊",
            "marker": "yes",
            "color": "#00e5ff",
            "glow": "rgba(0, 229, 255, 0.4)",
            "message": random.choice(MOTIVACIONES),
        }

    if polarity < -0.05:
        return {
            "title": "Un abrazo fuerte... déjame sacarte una sonrisa",
            "feeling": "Parece un momento difícil",
            "emoji": "💛",
            "marker": "no",
            "color": "#bf5af2",
            "glow": "rgba(191, 90, 242, 0.4)",
            "message": f"Siento que no estés teniendo el mejor día. Para animarte un poco, mira este chiste:\n\n{random.choice(CHISTES)}",
        }

    return {
        "title": "Te escucho con atención...",
        "feeling": "Tranquilo y reflexivo",
        "emoji": "💬",
        "marker": "thinking",
        "color": "#64d2ff",
        "glow": "rgba(100, 210, 255, 0.35)",
        "message": random.choice(CONVERSACION_NEUTRAL),
    }


# -----------------------------------------------------------------------------
# ESTADO DE SESIÓN (Permite interactuar con los chips de prueba rápida)
# -----------------------------------------------------------------------------
if "phrase_input" not in st.session_state:
    st.session_state.phrase_input = ""


def set_quick_phrase(phrase: str):
    st.session_state.phrase_input = phrase


# -----------------------------------------------------------------------------
# ENCABEZADO Y ENTRADA PRINCIPAL
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

# Fila interactiva de chips de prueba rápida
render_clean_html(
    """
    <div style="text-align: center; margin-bottom: 12px;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64d2ff; letter-spacing: 2px; text-transform: uppercase;">
            ⚡ Pruebas rápidas:
        </span>
    </div>
    """
)

chip_cols = st.columns(4)
with chip_cols[0]:
    if st.button("🎉 ¡Tuve un día genial!", use_container_width=True):
        set_quick_phrase("¡Hoy fue un día increíble y lleno de energía!")
        st.rerun()

with chip_cols[1]:
    if st.button("🌧️ Me siento desanimado", use_container_width=True):
        set_quick_phrase("Hoy me siento triste y sin ganas de nada...")
        st.rerun()

with chip_cols[2]:
    if st.button("⚡ Estoy muy molesto", use_container_width=True):
        set_quick_phrase("Tengo mucha rabia con una situación injusta")
        st.rerun()

with chip_cols[3]:
    if st.button("🍃 Una tarde tranquila", use_container_width=True):
        set_quick_phrase("Es un día tranquilo, pensando en mis metas")
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

# Procesamiento del sentimiento
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
        "color": "#00f0ff",
        "glow": "rgba(0, 240, 255, 0.35)",
        "message": "Cuéntame lo que estás sintiendo o cómo estuvo tu día. Aquí estaré listo para acompañarte y responderte.",
    }

active_lottie = get_mood_slice(base_animation, response["marker"])

# -----------------------------------------------------------------------------
# INYECCIÓN DINÁMICA DE ESTILOS CSS SEGÚN EL ÁNIMO ACTIVO
# -----------------------------------------------------------------------------
MOOD_THEME_CSS = r"""
<style>
:root {
    --mood-color: __COLOR__;
    --mood-glow: __GLOW__;
}

/* Borde exterior interactivo con gradiente vivo */
.cyber-card-outer {
    position: relative;
    border-radius: 24px;
    padding: 2px;
    background: linear-gradient(135deg, var(--mood-color) 0%, rgba(255,255,255,0.05) 50%, var(--mood-color) 100%);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7), 0 0 35px var(--mood-glow);
    transition: all 0.5s ease;
    margin-bottom: 16px;
}

.cyber-card-outer:hover {
    transform: translateY(-3px);
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.8), 0 0 50px var(--mood-glow);
}

.cyber-card-inner {
    background: rgba(11, 16, 28, 0.92);
    border-radius: 22px;
    padding: 24px;
    backdrop-filter: blur(20px);
}

/* Pedestal Holográfico para el Robot */
.holo-chamber {
    position: relative;
    width: 100%;
    min-height: 360px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    border-radius: 22px;
    background: radial-gradient(circle at center, var(--mood-glow) 0%, rgba(5, 7, 12, 0.95) 75%);
}

/* Anillos concéntricos giratorios estilo holograma */
.holo-ring-1 {
    position: absolute;
    bottom: 22px;
    width: 210px;
    height: 50px;
    border-radius: 50%;
    border: 2px dashed var(--mood-color);
    box-shadow: 0 0 25px var(--mood-color), inset 0 0 15px var(--mood-color);
    animation: spinRing 12s linear infinite;
    opacity: 0.75;
    pointer-events: none;
}

.holo-ring-2 {
    position: absolute;
    bottom: 30px;
    width: 150px;
    height: 36px;
    border-radius: 50%;
    border: 1px solid var(--mood-color);
    box-shadow: 0 0 15px var(--mood-color);
    animation: spinRingReverse 8s linear infinite;
    opacity: 0.9;
    pointer-events: none;
}

@keyframes spinRing {
    0% { transform: rotateX(75deg) rotateZ(0deg); }
    100% { transform: rotateX(75deg) rotateZ(360deg); }
}

@keyframes spinRingReverse {
    0% { transform: rotateX(75deg) rotateZ(360deg); }
    100% { transform: rotateX(75deg) rotateZ(0deg); }
}

/* Emisor de luz inferior */
.holo-beam {
    position: absolute;
    bottom: 0;
    width: 170px;
    height: 120px;
    background: linear-gradient(0deg, var(--mood-glow) 0%, transparent 100%);
    filter: blur(14px);
    pointer-events: none;
}

/* Ecualizador de audio animado */
.audio-equalizer {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 22px;
    margin-right: 10px;
}

.audio-bar {
    width: 3px;
    background: var(--mood-color);
    box-shadow: 0 0 8px var(--mood-color);
    border-radius: 3px;
    animation: eqPulse 1s ease-in-out infinite alternate;
}

.audio-bar:nth-child(1) { height: 35%; animation-delay: 0.1s; }
.audio-bar:nth-child(2) { height: 90%; animation-delay: 0.3s; }
.audio-bar:nth-child(3) { height: 60%; animation-delay: 0.2s; }
.audio-bar:nth-child(4) { height: 100%; animation-delay: 0.4s; }
.audio-bar:nth-child(5) { height: 45%; animation-delay: 0.15s; }

@keyframes eqPulse {
    0% { transform: scaleY(0.4); }
    100% { transform: scaleY(1.1); }
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
    box-shadow: 0 0 15px var(--mood-color);
    transition: left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}
</style>
""".replace("__COLOR__", response["color"]).replace("__GLOW__", response["glow"])

render_clean_html(MOOD_THEME_CSS)


# -----------------------------------------------------------------------------
# ESCENARIO PRINCIPAL: ROBOT HOLOGRÁFICO & DIÁLOGO SINCRONIZADO
# -----------------------------------------------------------------------------
col_robo, col_dialogo = st.columns([1, 1.25], gap="large")

with col_robo:
    # Cámara holográfica del robot
    render_clean_html(
        f"""
        <div class="cyber-card-outer">
            <div class="cyber-card-inner" style="padding: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: {response['color']}; letter-spacing: 2px;">
                        ● RADAR ACTIVO
                    </span>
                    <span style="font-size: 0.85rem; font-weight: 700; color: #ffffff;">
                        {response['emoji']} {response['feeling']}
                    </span>
                </div>
                <div class="holo-chamber">
                    <div class="holo-beam"></div>
                    <div class="holo-ring-1"></div>
                    <div class="holo-ring-2"></div>
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
        st.info("Buscando animación Lottie...")

    # Puntero para la barra de polaridad (-1 a 1 mapeado a 0% a 100%)
    pin_percent = int(((polarity_val + 1.0) / 2.0) * 100)
    pin_percent = max(0, min(100, pin_percent))

    render_clean_html(
        f"""
                </div>
                <div style="margin-top: 14px; padding: 0 8px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.75rem; font-family: 'JetBrains Mono'; color: #7f97b2;">
                        <span>Negativo (-1.0)</span>
                        <span style="color: {response['color']}; font-weight: 700;">Ánimo: {polarity_val:+0.2f}</span>
                        <span>Positivo (+1.0)</span>
                    </div>
                    <div class="gauge-track">
                        <div class="gauge-pin" style="left: calc({pin_percent}% - 9px);"></div>
                    </div>
                </div>
            </div>
        </div>
        """
    )


with col_dialogo:
    render_clean_html(
        f"""
        <div class="cyber-card-outer">
            <div class="cyber-card-inner">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="color: {response['color']}; font-family: 'Orbitron'; font-size: 0.85rem; font-weight: 800; letter-spacing: 1.5px;">
                        {response['emoji']} TU COMPAÑERO DICE
                    </span>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: rgba(0,0,0,0.4); padding: 5px 12px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.1); color: #c4d7ec;">
                        Subjetividad: {int(subjectivity_val * 100)}%
                    </span>
                </div>

                <h2 style="font-size: 1.55rem; font-weight: 700; margin: 0 0 12px 0; color: #ffffff; text-shadow: 0 0 15px rgba(255,255,255,0.25);">
                    {response['title']}
                </h2>

                <div style="font-size: 1.05rem; line-height: 1.6; color: #edf4fc; background: rgba(0,0,0,0.35); padding: 18px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 12px;">
                    {response['message'].replace(chr(10), '<br>')}
                </div>
            </div>
        </div>
        """
    )

    # REPRODUCCIÓN AUTOMÁTICA CON VOZ MASCULINA NEURAL & ECUALIZADOR ANIMADO
    if user_phrase and user_phrase.strip():
        selected_male_voice = st.session_state.get("preferred_voice", "es-ES-AlvaroNeural")
        spoken_text = f"{response['title']}. {response['message']}"
        voice_audio = get_speech_audio(spoken_text, voice_name=selected_male_voice)

        if voice_audio:
            render_clean_html(
                f"""
                <div style="display: flex; align-items: center; margin-top: 4px; margin-bottom: 6px;">
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
            <div style="background: rgba(100, 210, 255, 0.05); border-radius: 14px; padding: 12px 18px; border: 1px solid rgba(100, 210, 255, 0.2); margin-top: 8px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: {response['color']}; letter-spacing: 1.5px;">
                    TRADUCCIÓN ({selected_lang.upper()}):
                </div>
                <div style="font-size: 0.95rem; color: #ffffff; margin-top: 3px;">
                    "{translated_display}"
                </div>
            </div>
            """
        )


# -----------------------------------------------------------------------------
# BARRA LATERAL: AJUSTES Y GUÍA
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
        - **Euforia / Alegría:** Resplandor esmeralda y celebración de logros.
        - **Tristeza:** Resplandor amatista y dosis de humor reconfortante.
        - **Tensión / Rabia:** Resplandor carmesí y consejos de respiración y calma.
        - **Calma:** Resplandor cian y reflexión tranquila.
        """
    )
    st.caption("NOIR.AI // Python 3.11 // Cyber-Noir Companion")
