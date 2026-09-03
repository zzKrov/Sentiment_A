import os
import json
import copy
import random
from io import BytesIO
import streamlit as st
from streamlit_lottie import st_lottie
from textblob import TextBlob
from gtts import gTTS

# Compatibilidad con la sintaxis st.lottie de las diapositivas
st.lottie = st_lottie

# Motores de traducción resilientes para Python 3.11
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
# 1. HELPER HTML (Sin sangría para evitar bloques de código de Markdown)
# -----------------------------------------------------------------------------
def render_clean_html(html_str: str):
    clean = "".join(line.strip() for line in html_str.splitlines() if line.strip())
    st.markdown(clean, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. CONFIGURACIÓN Y ESTILO GLOWING NOIR (CENTRADO Y EMBEBIDO)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tu Compañero Emocional",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

NOIR_STYLE = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #05070c !important;
    color: #e6edf5 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    overflow-x: hidden;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* Centrado general para que en pantallas anchas no se disperse */
.block-container {
    max-width: 1150px !important;
    padding-top: 1.8rem !important;
    padding-bottom: 2.5rem !important;
    margin: 0 auto !important;
}

/* Partículas interactivas de fondo */
#noir-canvas-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 0;
    pointer-events: none;
}

.title-glow {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: 2px;
    background: linear-gradient(135deg, #ffffff 10%, #64d2ff 60%, #0077ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}

/* Estilo unificado para la tarjeta derecha */
.card-noir {
    background: rgba(13, 18, 30, 0.75);
    border: 1px solid rgba(100, 210, 255, 0.18);
    border-radius: 20px;
    padding: 24px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.7);
    margin-bottom: 12px;
}

/* Estilo que envuelve directamente el contenedor nativo del robot */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(13, 18, 30, 0.75) !important;
    border: 1px solid rgba(100, 210, 255, 0.18) !important;
    border-radius: 20px !important;
    padding: 20px !important;
    backdrop-filter: blur(16px) !important;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.7) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
}

/* Centrado y resplandor para el widget de Lottie */
div[data-testid="stLottie"], iframe[title="streamlit_lottie.st_lottie"] {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    margin: 0 auto !important;
    filter: drop-shadow(0 0 25px rgba(100, 210, 255, 0.35));
}

.stTextInput input {
    background: rgba(13, 19, 33, 0.85) !important;
    border: 1px solid rgba(100, 210, 255, 0.25) !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-size: 1.05rem !important;
    padding: 14px 18px !important;
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
                alpha: 0.85,
                decay: Math.random() * 0.025 + 0.015,
                vx: (Math.random() - 0.5) * 1.2,
                vy: (Math.random() - 0.5) * 1.2
            });
        }
    });

    for (let i = 0; i < 50; i++) {
        particles.push({
            x: Math.random() * w,
            y: Math.random() * h,
            r: Math.random() * 1.5 + 0.5,
            vx: (Math.random() - 0.5) * 0.2,
            vy: (Math.random() - 0.5) * 0.2,
            alpha: Math.random() * 0.5 + 0.2
        });
    }

    function animate() {
        ctx.clearRect(0, 0, w, h);

        for (let p of particles) {
            p.x += p.vx;
            p.y += p.vy;
            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(100, 210, 255, " + (p.alpha * 0.3) + ")";
            ctx.shadowBlur = 6;
            ctx.shadowColor = "#64d2ff";
            ctx.fill();
        }

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
            ctx.fillStyle = "rgba(0, 240, 255, " + (t.alpha * 0.6) + ")";
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

render_clean_html(NOIR_STYLE)


# -----------------------------------------------------------------------------
# 3. CARGA DE ARCHIVO Y ELIMINACIÓN DE BOTONES DEL LOTTIE
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_lottie():
    """Busca el archivo Lottie y apaga las capas de botones que vienen en la base."""
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

    # Búsqueda recursiva en subcarpetas
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

    # Supresión de capas correspondientes a los botones dibujados (capas 1 a 10)
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
    """Segmenta los fotogramas para reproducir la emoción correspondiente."""
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
# 4. TRADUCCIÓN Y VOZ SINTETIZADA
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


def get_speech_audio(text: str, lang: str = "es") -> bytes:
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    except Exception:
        return b""


# -----------------------------------------------------------------------------
# 5. MENSAJES AMIGABLES Y EMPÁTICOS
# -----------------------------------------------------------------------------
CHISTES = [
    "—Papá, ¿qué se siente tener un hijo tan inteligente? —No sé hijo, pregúntale a tu abuelo.",
    "¿Qué le dice un bit a otro? —Nos vemos en el bus.",
    "¿Por qué los pájaros no usan WhatsApp? —Porque ya tienen Twitter.",
    "¿Cómo maldice un informático frustrado? —¡Me cago en el bit que te parió!",
    "¿Qué hace una abeja en el gimnasio? —¡Zumba!",
    "No te desanimes: hasta el código más profesional tuvo cientos de errores antes de funcionar.",
]

MOTIVACIONES = [
    "¡Qué alegría leerte así! Aprovecha este buen momento para darte un gusto, compartir tu alegría o avanzar en eso que tanto querías.",
    "¡Esa es la actitud! Con esa buena energía contagias a cualquiera. ¡Sigue disfrutando tu día!",
    "¡Se nota que las cosas van bien! Mantén ese optimismo y celebra tus pequeños y grandes logros.",
]

CONSEJOS_CALMA = [
    "Uff, es normal sentirse así cuando las cosas salen mal o son injustas. Respira hondo, bebe un vaso de agua fresca y tómate cinco minutos antes de seguir.",
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
            "color": "#ff453a",
            "message": random.choice(CONSEJOS_CALMA),
        }

    if any(k in lower_text for k in EXCITED_WORDS) or (polarity >= 0.5):
        return {
            "title": "¡Qué gran noticia, me alegro mucho!",
            "feeling": "¡Mucha alegría y emoción!",
            "emoji": "🎉",
            "marker": "jump",
            "color": "#30d158",
            "message": random.choice(MOTIVACIONES),
        }

    if polarity > 0.05:
        return {
            "title": "¡Qué gusto leer esto!",
            "feeling": "Buena vibra detectada",
            "emoji": "😊",
            "marker": "yes",
            "color": "#64d2ff",
            "message": random.choice(MOTIVACIONES),
        }

    if polarity < -0.05:
        return {
            "title": "Un abrazo fuerte... déjame sacarte una sonrisa",
            "feeling": "Parece un momento difícil",
            "emoji": "💛",
            "marker": "no",
            "color": "#bf5af2",
            "message": f"Siento que no estés teniendo el mejor día. Para animarte un poco, mira este chiste:\n\n{random.choice(CHISTES)}",
        }

    return {
        "title": "Te escucho con atención...",
        "feeling": "Tranquilo y reflexivo",
        "emoji": "💬",
        "marker": "thinking",
        "color": "#00f0ff",
        "message": random.choice(CONVERSACION_NEUTRAL),
    }


# -----------------------------------------------------------------------------
# 6. ENCABEZADO Y ENTRADA DE TEXTO
# -----------------------------------------------------------------------------
render_clean_html(
    """
    <div style="text-align: center; margin-top: 5px; margin-bottom: 22px;">
        <div class="title-glow">TU COMPAÑERO EMOCIONAL</div>
        <p style="color: #8da4be; font-size: 0.95rem; margin-top: 2px;">
            Escribe cómo te sientes o cómo fue tu día y presiona Enter para conversar.
        </p>
    </div>
    """
)

col_input, col_target = st.columns([3.2, 1], gap="medium")

with col_input:
    user_phrase = st.text_input(
        label="¿Qué tienes en mente?",
        placeholder="Ej: ¡Hoy fue un día increíble en el trabajo! / Estoy un poco cansado de todo...",
        key="main_input",
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

# Procesamiento de sentimiento en tiempo real
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
        "color": "#64d2ff",
        "message": "Cuéntame lo que estás sintiendo o lo que hiciste hoy. Te escucharé con atención y aquí estaré para responderte.",
    }

# Preparación de la animación
active_lottie = get_mood_slice(base_animation, response["marker"])


# -----------------------------------------------------------------------------
# 7. VISTA PRINCIPAL: ROBOT EMBEBIDO DENTRO DE SU TARJETA Y ALINEADO
# -----------------------------------------------------------------------------
col_robo, col_dialogo = st.columns([1, 1.3], gap="large")

with col_robo:
    # Contenedor nativo que envuelve el robot y su estado en UNA sola tarjeta
    with st.container(border=True):
        render_clean_html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 4px;">
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64d2ff; letter-spacing: 1px;">
                    ESTADO EN VIVO
                </span>
                <span style="font-size: 0.85rem; font-weight: 700; color: {response['color']};">
                    {response['emoji']} {response['feeling']}
                </span>
            </div>
            """
        )

        if active_lottie:
            # st.lottie dentro del cuadro diseñado, centrado y a la altura del texto
            st.lottie(
                active_lottie,
                width=260,
                height=260,
                key=f"companion_lottie_{response['marker']}",
            )
        else:
            st.info("Buscando animación Lottie en la carpeta del proyecto...")

        render_clean_html(
            f"""
            <div style="text-align: center; margin-top: 4px;">
                <span style="font-size: 0.8rem; color: #8da4be; font-family: 'JetBrains Mono', monospace;">
                    Ánimo detectado: {polarity_val:+0.2f}
                </span>
            </div>
            """
        )


with col_dialogo:
    # Tarjeta de diálogo a la misma altura exacta
    render_clean_html(
        f"""
        <div class="card-noir" style="border-left: 4px solid {response['color']};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="color: {response['color']}; font-weight: 700; font-size: 0.9rem;">
                    {response['emoji']} TU COMPAÑERO DICE:
                </span>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; background: rgba(0,0,0,0.35); padding: 4px 10px; border-radius: 12px; color: #a4bedc;">
                    Subjetividad: {subjectivity_val}
                </span>
            </div>

            <h2 style="font-size: 1.55rem; font-weight: 700; margin: 0 0 12px 0; color: #ffffff;">
                {response['title']}
            </h2>

            <div style="font-size: 1.05rem; line-height: 1.6; color: #eaf1fa; background: rgba(0,0,0,0.3); padding: 16px; border-radius: 14px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 10px;">
                {response['message'].replace(chr(10), '<br>')}
            </div>
        </div>
        """
    )

    # Reproductor de voz
    if user_phrase and user_phrase.strip():
        spoken_text = f"{response['title']}. {response['message']}"
        voice_audio = get_speech_audio(spoken_text, lang="es")
        if voice_audio:
            st.caption("🔊 Escuchar la respuesta:")
            st.audio(voice_audio, format="audio/mp3")

    # Traducción
    if translated_display:
        render_clean_html(
            f"""
            <div style="background: rgba(100, 210, 255, 0.05); border-radius: 12px; padding: 12px 18px; border: 1px solid rgba(100, 210, 255, 0.2); margin-top: 10px;">
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #64d2ff; letter-spacing: 1px;">
                    TU MENSAJE EN {selected_lang.upper()}:
                </div>
                <div style="font-size: 0.95rem; color: #ffffff; margin-top: 4px;">
                    "{translated_display}"
                </div>
            </div>
            """
        )


# -----------------------------------------------------------------------------
# 8. BARRA LATERAL INFORMATIVA
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 💡 ¿Cómo funciona?")
    st.info(
        """
        **Análisis de Ánimo:**
        El compañero analiza el texto ingresado para entender cómo te sientes:
        - **Positivo (> 0):** Celebrará tus logros y te motivará a seguir con esa buena energía.
        - **Triste (< 0):** Te acompañará y te contará un chiste para levantarte el ánimo.
        - **Enojado o Frustrado:** Te ofrecerá palabras de calma y consejos para relajarte.
        - **Neutral (~ 0):** Conversará contigo de forma abierta y reflexiva.
        """
    )
    st.markdown("---")
    st.caption("NOIR.AI // Python 3.11 // TextBlob & Streamlit-Lottie")
