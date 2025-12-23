import streamlit as st
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="🫒 Olivetti", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
DEFAULTS = {
    "text": "",
    "junk": "",
    "synopsis": "",
    "genre": "Literary",
    "world": "",
    "characters": "",
    "outline": "",
    "style": "Neutral",
    "voice": "Literary",
    "trained": "— None —",
    "sample": "",
    "intensity": 0.5,
    "voice_lock": False,
    "focus": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# AI CORE
# ============================================================
def run_ai(action):
    style_block = f"""
STYLE:
Writing style: {st.session_state.style}
Genre voice: {st.session_state.voice}
Intensity: {st.session_state.intensity}
"""

    if st.session_state.voice_lock:
        style_block += "\nIMPORTANT: Do not change voice or tone."

    if st.session_state.sample:
        style_block += f"\nMatch this sample:\n{st.session_state.sample}"

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

    prompt = f"""
{style_block}

TASK:
{PROMPTS[action]}

TEXT:
{st.session_state.text}
"""

    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a professional fiction editor."},
            {"role": "user", "content": prompt}
        ],
        temperature=st.session_state.intensity
    )

    st.session_state.text = r.output_text.strip()

# ============================================================
# TOP BAR
# ============================================================
top = st.columns([2,1,1,1,1])
top[0].markdown("## 🫒 **Olivetti**")
top[1].button("New Project", key="new")
top[2].button("Rough Draft", key="rough")
top[3].button("First Edit", key="edit")
top[4].button("Final Draft", key="final")

st.divider()

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.3, 3.4, 1.3], gap="large")

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    with st.expander("📖 Story Bible", expanded=True):
        st.text_area("Junk Drawer", key="junk", height=80)
        st.text_area("Synopsis", key="synopsis", height=80)
        st.selectbox("Genre / Style", ["Literary","Noir","Thriller","Comedy"], key="genre")
        st.text_area("World Elements", key="world", height=80)
        st.text_area("Characters", key="characters", height=80)
        st.text_area("Outline", key="outline", height=120)

# ============================================================
# CENTER — WRITING DESK
# ============================================================
with center:
    st.markdown("### ✍️ Writing Desk")
    st.text_area("", key="text", height=560)

    b1 = st.columns(5)
    if b1[0].button("Write"): run_ai("write")
    if b1[1].button("Rewrite"): run_ai("rewrite")
    if b1[2].button("Expand"): run_ai("expand")
    if b1[3].button("Rephrase"): run_ai("rephrase")
    if b1[4].button("Describe"): run_ai("describe")

    b2 = st.columns(5)
    if b2[0].button("Spell Check"): run_ai("spell")
    if b2[1].button("Grammar Check"): run_ai("grammar")
    if b2[2].button("Find / Replace"): run_ai("find")
    if b2[3].button("Synonyms"): run_ai("syn")
    if b2[4].button("Sentence Improve"): run_ai("sentence")

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
with right:
    with st.expander("🎭 Voice Bible", expanded=True):
        st.selectbox("Writing Style", ["Neutral","Minimal","Expressive"], key="style")
        st.selectbox("Genre Voice", ["Literary","Hardboiled","Poetic"], key="voice")
        st.selectbox("Trained Voices", ["— None —"], key="trained")
        st.text_area("Match My Style", key="sample", height=80)
        st.slider("Intensity", 0.0, 1.0, key="intensity")
        st.toggle("Voice Lock", key="voice_lock")

# ============================================================
# FOCUS MODE
# ============================================================
if st.session_state.focus:
    st.markdown(
        "<style>[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True
    )

st.divider()
f = st.columns(2)
f[0].button("🔒 Focus Mode", on_click=lambda: st.session_state.update({"focus": True}))
f[1].caption("Olivetti — AI Writing Desk")
