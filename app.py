import streamlit as st
from openai import OpenAI
import time
import os
from typing import Dict, Any

# ============================================================
# APP CONFIG (LOCKED)
# ============================================================
st.set_page_config(
    page_title="🫒 Olivetti",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ENV / CLIENT (SAFE INIT)
# ============================================================
API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI() if API_KEY else None

# ============================================================
# CONSTANTS (HARD LIMITS)
# ============================================================
MAX_TEXT_CHARS = 12000
MAX_VERSIONS = 100
AI_COOLDOWN = 2.0
AI_TIMEOUT = 20.0

# ============================================================
# STATE MANAGEMENT (SINGLE SOURCE OF TRUTH)
# ============================================================
def ensure_state(key: str, default: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = default

STATE_SCHEMA: Dict[str, Any] = {
    "text": "",
    "versions": [],
    "junk": "",
    "synopsis": "",
    "world": "",
    "characters": "",
    "outline": "",
    "style": "Neutral",
    "genre": "Literary",
    "voice": "Literary",
    "trained_voices": {},
    "trained_voice": "— None —",
    "sample": "",
    "intensity": 0.5,
    "voice_lock": False,
    "focus": False,
    "last_ai": 0.0,
    "last_save": 0.0,
}

for k, v in STATE_SCHEMA.items():
    ensure_state(k, v)

# ============================================================
# CORE SAFETY UTILITIES
# ============================================================
def bounded(text: str) -> str:
    return text[:MAX_TEXT_CHARS] if isinstance(text, str) else ""

def snapshot(text: str) -> None:
    if not text:
        return
    versions = st.session_state.versions
    if versions and versions[-1] == text:
        return
    versions.append(text)
    if len(versions) > MAX_VERSIONS:
        st.session_state.versions = versions[-MAX_VERSIONS:]

def autosave() -> None:
    snapshot(bounded(st.session_state.text))
    st.session_state.last_save = time.time()

def ai_allowed() -> bool:
    now = time.time()
    if now - st.session_state.last_ai < AI_COOLDOWN:
        return False
    st.session_state.last_ai = now
    return True

# ============================================================
# VOICE ENGINE (PURE / DETERMINISTIC)
# ============================================================
def voice_profile() -> str:
    profile = [
        f"Writing Style: {st.session_state.style}",
        f"Genre Voice: {st.session_state.voice}",
        f"Intensity: {st.session_state.intensity}",
    ]

    if st.session_state.trained_voice != "— None —":
        profile.append(
            "Trained Voice:\n" +
            st.session_state.trained_voices.get(
                st.session_state.trained_voice, ""
            )
        )
    elif st.session_state.sample.strip():
        profile.append("Match This Style:\n" + st.session_state.sample)

    if st.session_state.voice_lock:
        profile.append("IMPORTANT: Voice must remain consistent.")

    return "\n".join(profile)

# ============================================================
# AI EXECUTION (ATOMIC + ISOLATED)
# ============================================================
PROMPTS = {
    "write": "Continue writing naturally.",
    "rewrite": "Rewrite for clarity and strength.",
    "expand": "Expand with more depth.",
    "rephrase": "Rephrase without altering meaning.",
    "describe": "Add vivid sensory description.",
    "spell": "Fix spelling only.",
    "grammar": "Fix grammar only.",
    "find": "Improve consistency.",
    "syn": "Suggest stronger word choices.",
    "sentence": "Improve sentence flow.",
}

def run_ai(action: str) -> None:
    if not client or action not in PROMPTS:
        return
    if not ai_allowed():
        return

    source = bounded(st.session_state.text)
    if not source.strip():
        return

    prompt = f"""
VOICE PROFILE:
{voice_profile()}

TASK:
{PROMPTS[action]}

TEXT:
{source}
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": "You are a professional fiction editor."},
                {"role": "user", "content": prompt},
            ],
            temperature=float(st.session_state.intensity),
            timeout=AI_TIMEOUT,
        )

        output = (response.output_text or "").strip()
        if output:
            snapshot(source)
            st.session_state.text = bounded(output)
            autosave()

    except Exception:
        # Production rule: never destroy user text
        pass

# ============================================================
# TOP BAR (LOCKED)
# ============================================================
t = st.columns([2,1,1,1,1])
t[0].markdown("## 🫒 **Olivetti**")
t[1].button("New Project", key="top_new")
t[2].button("Rough Draft", key="top_rough")
t[3].button("First Edit", key="top_edit")
t[4].button("Final Draft", key="top_final")

st.divider()

# ============================================================
# LAYOUT (FINAL)
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
                     ["Literary","Noir","Thriller","Comedy"],
                     key="genre")
        st.text_area("World Elements", key="world", height=70, on_change=autosave)
        st.text_area("Characters", key="characters", height=70, on_change=autosave)
        st.text_area("Outline", key="outline", height=120, on_change=autosave)

# ============================================================
# CENTER — WRITING DESK (ALWAYS ON)
# ============================================================
with center:
    st.markdown("### ✍️ Writing Desk")
    st.text_area("", key="text", height=620, on_change=autosave)

    r1 = st.columns(5)
    r1[0].button("Write", on_click=lambda: run_ai("write"))
    r1[1].button("Rewrite", on_click=lambda: run_ai("rewrite"))
    r1[2].button("Expand", on_click=lambda: run_ai("expand"))
    r1[3].button("Rephrase", on_click=lambda: run_ai("rephrase"))
    r1[4].button("Describe", on_click=lambda: run_ai("describe"))

    r2 = st.columns(5)
    r2[0].button("Spell Check", on_click=lambda: run_ai("spell"))
    r2[1].button("Grammar Check", on_click=lambda: run_ai("grammar"))
    r2[2].button("Find / Replace", on_click=lambda: run_ai("find"))
    r2[3].button("Synonyms", on_click=lambda: run_ai("syn"))
    r2[4].button("Sentence Improve", on_click=lambda: run_ai("sentence"))

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
with right:
    with st.expander("🎭 Voice Bible", expanded=True):
        st.selectbox("Writing Style",
                     ["Neutral","Minimal","Expressive"],
                     key="style")
        st.selectbox("Genre Voice",
                     ["Literary","Hardboiled","Poetic"],
                     key="voice")

        voice_list = ["— None —"] + list(st.session_state.trained_voices.keys())
        st.selectbox("Trained Voices", voice_list, key="trained_voice")

        st.text_area("Match My Style", key="sample", height=70)

        c1, c2 = st.columns(2)
        name = c1.text_input("Save Voice As", key="voice_name")
        if c2.button("Train Voice"):
            if name and st.session_state.sample.strip():
                st.session_state.trained_voices[name] = st.session_state.sample
                st.session_state.trained_voice = name
                autosave()

        st.slider("Intensity", 0.0, 1.0, key="intensity")
        st.toggle("Voice Lock", key="voice_lock")

# ============================================================
# FOCUS MODE (HARD ISOLATION)
# ============================================================
if st.session_state.focus:
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True
    )

st.divider()
b = st.columns(2)
b[0].button("🔒 Focus Mode", on_click=lambda: st.session_state.update({"focus": True}))
b[1].caption("Olivetti — Production Core Locked")
