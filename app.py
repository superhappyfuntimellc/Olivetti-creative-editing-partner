import streamlit as st
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="🫒 Olivetti", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE (SAFE INIT)
# ============================================================
def init(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

init("text", "")
init("junk", "")
init("synopsis", "")
init("genre", "Literary")
init("world", "")
init("characters", "")
init("outline", "")
init("style", "Neutral")
init("voice", "Literary")
init("trained_voices", {})
init("trained_voice", "— None —")
init("sample", "")
init("intensity", 0.5)
init("voice_lock", False)
init("focus", False)

# ============================================================
# VOICE ENGINE (PURE / SAFE)
# ============================================================
def build_voice_block():
    parts = [
        f"Writing Style: {st.session_state.style}",
        f"Genre Voice: {st.session_state.voice}",
        f"Intensity: {st.session_state.intensity}",
    ]

    if st.session_state.trained_voice != "— None —":
        parts.append(
            f"Use this trained voice:\n{st.session_state.trained_voices.get(st.session_state.trained_voice,'')}"
        )
    elif st.session_state.sample.strip():
        parts.append(f"Match this sample:\n{st.session_state.sample}")

    if st.session_state.voice_lock:
        parts.append("IMPORTANT: Do not change voice or tone.")

    return "\n".join(parts)

# ============================================================
# AI CORE (GUARDED)
# ============================================================
PROMPTS = {
    "write": "Continue writing naturally.",
    "rewrite": "Rewrite for clarity and strength.",
    "expand": "Expand with more depth and detail.",
    "rephrase": "Rephrase without changing meaning.",
    "describe": "Add vivid sensory description.",
    "spell": "Fix spelling only.",
    "grammar": "Fix grammar only.",
    "find": "Improve consistency and phrasing.",
    "syn": "Suggest better word choices inline.",
    "sentence": "Improve sentence flow and rhythm.",
}

def run_ai(action):
    if action not in PROMPTS:
        return

    prompt = f"""
VOICE PROFILE:
{build_voice_block()}

TASK:
{PROMPTS[action]}

TEXT:
{st.session_state.text}
"""

    try:
        r = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": "You are a professional fiction editor."},
                {"role": "user", "content": prompt},
            ],
            temperature=st.session_state.intensity,
        )
        st.session_state.text = (r.output_text or "").strip()
    except Exception:
        pass

# ============================================================
# TOP BAR
# ============================================================
top = st.columns([2, 1, 1, 1, 1])
top[0].markdown("## 🫒 **Olivetti**")
top[1].button("New Project")
top[2].button("Rough Draft")
top[3].button("First Edit")
top[4].button("Final Draft")

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
        st.text_area("Junk Drawer", key="junk", height=80)
        st.text_area("Synopsis", key="synopsis", height=80)
        st.selectbox(
            "Genre / Style",
            ["Literary", "Noir", "Thriller", "Comedy"],
            key="genre",
        )
        st.text_area("World Elements", key="world", height=80)
        st.text_area("Characters", key="characters", height=80)
        st.text_area("Outline", key="outline", height=120)

# ============================================================
# CENTER — WRITING DESK (ALWAYS VISIBLE)
# ============================================================
with center:
    st.markdown("### ✍️ Writing Desk")
    st.text_area("", key="text", height=560)

    row1 = st.columns(5)
    if row1[0].button("Write"): run_ai("write")
    if row1[1].button("Rewrite"): run_ai("rewrite")
    if row1[2].button("Expand"): run_ai("expand")
    if row1[3].button("Rephrase"): run_ai("rephrase")
    if row1[4].button("Describe"): run_ai("describe")

    row2 = st.columns(5)
    if row2[0].button("Spell Check"): run_ai("spell")
    if row2[1].button("Grammar Check"): run_ai("grammar")
    if row2[2].button("Find / Replace"): run_ai("find")
    if row2[3].button("Synonyms"): run_ai("syn")
    if row2[4].button("Sentence Improve"): run_ai("sentence")

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

        voice_list = ["— None —"] + list(st.session_state.trained_voices.keys())
        st.selectbox("Trained Voices", voice_list, key="trained_voice")

        st.text_area("Match My Style", key="sample", height=80)

        col_a, col_b = st.columns(2)
        with col_a:
            voice_name = st.text_input("Save Voice As")
        with col_b:
            if st.button("Train Voice"):
                if voice_name and st.session_state.sample.strip():
                    st.session_state.trained_voices[voice_name] = st.session_state.sample
                    st.session_state.trained_voice = voice_name

        st.slider("Intensity", 0.0, 1.0, key="intensity")
        st.toggle("Voice Lock", key="voice_lock")

# ============================================================
# FOCUS MODE (SAFE)
# ============================================================
if st.session_state.focus:
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True,
    )

st.divider()
foot = st.columns(2)
foot[0].button("🔒 Focus Mode", on_click=lambda: st.session_state.update({"focus": True}))
foot[1].caption("Olivetti — Stable Build")
