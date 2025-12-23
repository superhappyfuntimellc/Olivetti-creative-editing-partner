import streamlit as st
from openai import OpenAI
import time
import os
import copy

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="🫒 Olivetti", layout="wide")

API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI() if API_KEY else None

# ============================================================
# CONSTANTS
# ============================================================
MAX_TEXT_CHARS = 12000
AI_COOLDOWN_SEC = 2.0
MAX_VERSIONS = 50

# ============================================================
# SESSION INIT (DEFENSIVE)
# ============================================================
def init(k, v):
    if k not in st.session_state:
        st.session_state[k] = v

DEFAULTS = {
    "text": "",
    "versions": [],
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
    "last_save": 0.0,
    "last_ai_call": 0.0,
}

for k, v in DEFAULTS.items():
    init(k, v)

# ============================================================
# VERSIONING (INVISIBLE, SAFE)
# ============================================================
def snapshot(text):
    if not text:
        return
    versions = st.session_state.versions
    if versions and versions[-1] == text:
        return
    versions.append(text)
    if len(versions) > MAX_VERSIONS:
        st.session_state.versions = versions[-MAX_VERSIONS:]

def autosave():
    text = st.session_state.text
    if isinstance(text, str):
        snapshot(text[:MAX_TEXT_CHARS])
        st.session_state.last_save = time.time()

# ============================================================
# VOICE ENGINE (PURE)
# ============================================================
def build_voice_block():
    parts = [
        f"Writing Style: {st.session_state.style}",
        f"Genre Voice: {st.session_state.voice}",
        f"Intensity: {float(st.session_state.intensity)}",
    ]

    if st.session_state.trained_voice != "— None —":
        parts.append(
            f"Trained Voice:\n{st.session_state.trained_voices.get(st.session_state.trained_voice,'')}"
        )
    elif st.session_state.sample.strip():
        parts.append(f"Match This Style:\n{st.session_state.sample}")

    if st.session_state.voice_lock:
        parts.append("IMPORTANT: Maintain voice exactly.")

    return "\n".join(parts)

# ============================================================
# AI CORE (ATOMIC + SAFE)
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

def can_call_ai():
    now = time.time()
    if now - st.session_state.last_ai_call < AI_COOLDOWN_SEC:
        return False
    st.session_state.last_ai_call = now
    return True

def run_ai(action):
    if not client or action not in PROMPTS:
        return

    source_text = st.session_state.text
    if not isinstance(source_text, str) or not source_text.strip():
        return

    if not can_call_ai():
        return

    safe_text = source_text[:MAX_TEXT_CHARS]

    prompt = f"""
VOICE PROFILE:
{build_voice_block()}

TASK:
{PROMPTS[action]}

TEXT:
{safe_text}
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

        # ATOMIC COMMIT
        if isinstance(output, str) and output.strip():
            snapshot(safe_text)
            st.session_state.text = output[:MAX_TEXT_CHARS]
            autosave()

    except Exception:
        # Silent fail: text remains untouched
        pass

# ============================================================
# TOP BAR (UNCHANGED)
# ============================================================
top = st.columns([2,1,1,1,1])
top[0].markdown("## 🫒 **Olivetti**")
top[1].button("New Project", key="top_new")
top[2].button("Rough Draft", key="top_rough")
top[3].button("First Edit", key="top_edit")
top[4].button("Final Draft", key="top_final")

st.divider()

# ============================================================
# LAYOUT (LOCKED)
# ============================================================
left, center, right = st.columns([1.3, 3.4, 1.3], gap="large")

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    with st.expander("📖 Story Bible", expanded=True):
        st.text_area("Junk Drawer", key="junk", height=70, on_change=autosave)
        st.text_area("Synopsis", key="synopsis", height=70, on_change=autosave)
        st.selectbox("Genre / Style",
                     ["Literary","Noir","Thriller","Comedy"], key="genre")
        st.text_area("World Elements", key="world", height=70, on_change=autosave)
        st.text_area("Characters", key="characters", height=70, on_change=autosave)
        st.text_area("Outline", key="outline", height=120, on_change=autosave)

# ============================================================
# CENTER — WRITING DESK (ALWAYS VISIBLE)
# ============================================================
with center:
    st.markdown("### ✍️ Writing Desk")
    st.text_area("", key="text", height=600, on_change=autosave)

    r1 = st.columns(5)
    if r1[0].button("Write"): run_ai("write")
    if r1[1].button("Rewrite"): run_ai("rewrite")
    if r1[2].button("Expand"): run_ai("expand")
    if r1[3].button("Rephrase"): run_ai("rephrase")
    if r1[4].button("Describe"): run_ai("describe")

    r2 = st.columns(5)
    if r2[0].button("Spell Check"): run_ai("spell")
    if r2[1].button("Grammar Check"): run_ai("grammar")
    if r2[2].button("Find / Replace"): run_ai("find")
    if r2[3].button("Synonyms"): run_ai("syn")
    if r2[4].button("Sentence Improve"): run_ai("sentence")

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
with right:
    with st.expander("🎭 Voice Bible", expanded=True):
        st.selectbox("Writing Style", ["Neutral","Minimal","Expressive"], key="style")
        st.selectbox("Genre Voice", ["Literary","Hardboiled","Poetic"], key="voice")

        voices = ["— None —"] + list(st.session_state.trained_voices.keys())
        st.selectbox("Trained Voices", voices, key="trained_voice")

        st.text_area("Match My Style", key="sample", height=70)

        c1, c2 = st.columns(2)
        with c1:
            vname = st.text_input("Save Voice As")
        with c2:
            if st.button("Train Voice"):
                if vname and st.session_state.sample.strip():
                    st.session_state.trained_voices[vname] = st.session_state.sample
                    st.session_state.trained_voice = vname
                    autosave()

        st.slider("Intensity", 0.0, 1.0, key="intensity")
        st.toggle("Voice Lock", key="voice_lock")

# ============================================================
# FOCUS MODE
# ============================================================
if st.session_state.focus:
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True,
    )

st.divider()
f = st.columns(2)
f[0].button("🔒 Focus Mode", on_click=lambda: st.session_state.update({"focus": True}))
f[1].caption("Olivetti — Writing Core Locked")
