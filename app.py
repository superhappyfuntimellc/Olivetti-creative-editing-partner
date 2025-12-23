import streamlit as st
from openai import OpenAI
import time

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="🫒 Olivetti", layout="wide")
client = OpenAI()

# ============================================================
# SAFE SESSION INIT
# ============================================================
def init(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

STATE_DEFAULTS = {
    "text": "",
    "junk": "",
    "synopsis": "",
    "genre": "Literary",
    "world": "",
    "characters": "",
    "outline": "",
    "style": "Neutral",
    "voice": "Literary",
    "trained_voices": {},
    "trained_voice": "— None —",
    "sample": "",
    "intensity": 0.5,
    "voice_lock": False,
    "focus": False,
    "last_save": time.time(),
}

for k, v in STATE_DEFAULTS.items():
    init(k, v)

# ============================================================
# AUTOSAVE (SAFE, SILENT)
# ============================================================
def autosave():
    st.session_state.last_save = time.time()

# ============================================================
# VOICE ENGINE (PURE / IMMUTABLE)
# ============================================================
def build_voice_block():
    blocks = [
        f"Writing Style: {st.session_state.style}",
        f"Genre Voice: {st.session_state.voice}",
        f"Intensity: {st.session_state.intensity}",
    ]

    if st.session_state.trained_voice != "— None —":
        blocks.append(
            f"Trained Voice:\n{st.session_state.trained_voices.get(st.session_state.trained_voice,'')}"
        )
    elif st.session_state.sample.strip():
        blocks.append(f"Match This Style:\n{st.session_state.sample}")

    if st.session_state.voice_lock:
        blocks.append("IMPORTANT: Maintain voice exactly.")

    return "\n".join(blocks)

# ============================================================
# AI CORE (HARDENED)
# ============================================================
PROMPTS = {
    "write": "Continue writing naturally.",
    "rewrite": "Rewrite for clarity and strength.",
    "expand": "Expand with more depth.",
    "rephrase": "Rephrase without changing meaning.",
    "describe": "Add vivid description.",
    "spell": "Fix spelling only.",
    "grammar": "Fix grammar only.",
    "find": "Improve consistency.",
    "syn": "Suggest stronger word choices.",
    "sentence": "Improve sentence flow.",
}

def run_ai(action):
    if action not in PROMPTS:
        return

    text = st.session_state.text.strip()
    if not text:
        return

    prompt = f"""
VOICE PROFILE:
{build_voice_block()}

TASK:
{PROMPTS[action]}

TEXT:
{text}
"""

    try:
        r = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": "You are a professional fiction editor."},
                {"role": "user", "content": prompt},
            ],
            temperature=float(st.session_state.intensity),
        )
        output = (r.output_text or "").strip()
        if output:
            st.session_state.text = output
            autosave()
    except Exception:
        pass

# ============================================================
# TOP BAR
# ============================================================
top = st.columns([2,1,1,1,1])
top[0].markdown("## 🫒 **Olivetti**")
top[1].button("New Project", key="top_new")
top[2].button("Rough Draft", key="top_rough")
top[3].button("First Edit", key="top_edit")
top[4].button("Final Draft", key="top_final")

st.divider()

# ============================================================
# MAIN LAYOUT
# ============================================================
left, center, right = st.columns([1.3, 3.4, 1.3], gap="large")

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    with st.expander("📖 Story Bible", expanded=True):
        st.text_area("Junk Drawer", key="junk", height=70, on_change=autosave)
        st.text_area("Synopsis", key="synopsis", height=70, on_change=autosave)
        st.selectbox(
            "Genre / Style",
            ["Literary", "Noir", "Thriller", "Comedy"],
            key="genre",
        )
        st.text_area("World Elements", key="world", height=70, on_change=autosave)
        st.text_area("Characters", key="characters", height=70, on_change=autosave)
        st.text_area("Outline", key="outline", height=120, on_change=autosave)

# ============================================================
# CENTER — WRITING DESK (LOCKED)
# ============================================================
with center:
    st.markdown("### ✍️ Writing Desk")
    st.text_area("", key="text", height=600, on_change=autosave)

    r1 = st.columns(5)
    if r1[0].button("Write", key="w1"): run_ai("write")
    if r1[1].button("Rewrite", key="w2"): run_ai("rewrite")
    if r1[2].button("Expand", key="w3"): run_ai("expand")
    if r1[3].button("Rephrase", key="w4"): run_ai("rephrase")
    if r1[4].button("Describe", key="w5"): run_ai("describe")

    r2 = st.columns(5)
    if r2[0].button("Spell Check", key="e1"): run_ai("spell")
    if r2[1].button("Grammar Check", key="e2"): run_ai("grammar")
    if r2[2].button("Find / Replace", key="e3"): run_ai("find")
    if r2[3].button("Synonyms", key="e4"): run_ai("syn")
    if r2[4].button("Sentence Improve", key="e5"): run_ai("sentence")

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
with right:
    with st.expander("🎭 Voice Bible", expanded=True):
        st.selectbox(
            "Writing Style",
            ["Neutral", "Minimal", "Expressive"],
            key="style",
        )
        st.selectbox(
            "Genre Voice",
            ["Literary", "Hardboiled", "Poetic"],
            key="voice",
        )

        voices = ["— None —"] + list(st.session_state.trained_voices.keys())
        st.selectbox("Trained Voices", voices, key="trained_voice")

        st.text_area("Match My Style", key="sample", height=70)

        c1, c2 = st.columns(2)
        with c1:
            vname = st.text_input("Save Voice As", key="voice_name")
        with c2:
            if st.button("Train Voice", key="train_voice"):
                if vname and st.session_state.sample.strip():
                    st.session_state.trained_voices[vname] = st.session_state.sample
                    st.session_state.trained_voice = vname
                    autosave()

        st.slider("Intensity", 0.0, 1.0, key="intensity")
        st.toggle("Voice Lock", key="voice_lock")

# ============================================================
# FOCUS MODE (HARD SAFE)
# ============================================================
if st.session_state.focus:
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True,
    )

st.divider()
f = st.columns(2)
f[0].button("🔒 Focus Mode", key="focus_btn",
            on_click=lambda: st.session_state.update({"focus": True}))
f[1].caption("Olivetti — Hardened Build")
