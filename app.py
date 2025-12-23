import streamlit as st
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="🫒 Olivetti", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
if "text" not in st.session_state:
    st.session_state.text = ""

if "focus" not in st.session_state:
    st.session_state.focus = False

if "last_saved" not in st.session_state:
    st.session_state.last_saved = None

if "voices" not in st.session_state:
    st.session_state.voices = {}

if "active_voice" not in st.session_state:
    st.session_state.active_voice = None

# ============================================================
# AUTOSAVE
# ============================================================
def autosave():
    st.session_state.last_saved = datetime.now().strftime("%H:%M:%S")

# ============================================================
# AI CALL
# ============================================================
def ai_write(text, voice_data):
    style = ""
    temp = 0.5

    if voice_data:
        style = f"""
Match this writing voice:
{voice_data['sample']}
"""
        temp = 0.3 + voice_data["intensity"] * 0.6

    prompt = f"""
Continue writing the following text.
Do not summarize.
Do not explain.
Just write forward naturally.

{style}

TEXT:
{text}
"""

    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a professional novelist continuing a draft."},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )

    return text + "\n\n" + r.output_text

# ============================================================
# TOP BAR
# ============================================================
c1, c2, c3, c4, c5 = st.columns([1,1,1,1,2])
with c1: st.button("🆕 New")
with c2: st.button("📝 Draft")
with c3: st.button("✏️ Edit")
with c4: st.button("✅ Final")
with c5:
    if st.button("🎯 Focus"):
        st.session_state.focus = not st.session_state.focus

st.divider()

# ============================================================
# LAYOUT
# ============================================================
if st.session_state.focus:
    left, center, right = None, st.container(), None
else:
    left, center, right = st.columns([1.2, 3.6, 1.4])

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
if left:
    with left:
        with st.expander("📖 Story Bible", expanded=False):
            st.text_area("Characters", height=120)
            st.text_area("World / Setting", height=120)
            st.text_area("Plot Threads", height=120)

# ============================================================
# CENTER — WRITING DESK (ALWAYS VISIBLE)
# ============================================================
with center:
    st.subheader("🫒 Writing Desk")

    st.session_state.text = st.text_area(
        "",
        st.session_state.text,
        height=420,
        placeholder="Write freely. No project required.",
        on_change=autosave
    )

    if st.session_state.last_saved:
        st.caption(f"💾 Autosaved at {st.session_state.last_saved}")

    st.divider()

    b1, b2, b3, b4, b5 = st.columns(5)

    if b1.button("✍️ Write"):
        voice = None
        if st.session_state.active_voice:
            voice = st.session_state.voices[st.session_state.active_voice]

        with st.spinner("Writing…"):
            st.session_state.text = ai_write(
                st.session_state.text,
                voice
            )
            autosave()

    b2.button("🔁 Rewrite", disabled=True)
    b3.button("➕ Expand", disabled=True)
    b4.button("🔄 Rephrase", disabled=True)
    b5.button("🎨 Describe", disabled=True)

    e1, e2, e3, e4, e5 = st.columns(5)
    e1.button("🧹 Spell", disabled=True)
    e2.button("📐 Grammar", disabled=True)
    e3.button("🔍 Find", disabled=True)
    e4.button("📚 Synonym", disabled=True)
    e5.button("🧠 Sentence", disabled=True)

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
if right:
    with right:
        with st.expander("🎭 Voice Bible", expanded=True):

            voice_name = st.text_input("Voice Name")
            voice_sample = st.text_area("Training Sample", height=120)
            intensity = st.slider("Intensity", 0.0, 1.0, 0.5)

            if st.button("➕ Save Voice"):
                if voice_name and voice_sample:
                    st.session_state.voices[voice_name] = {
                        "sample": voice_sample,
                        "intensity": intensity
                    }
                    st.session_state.active_voice = voice_name

            if st.session_state.voices:
                st.divider()
                selected = st.selectbox(
                    "Active Voice",
                    list(st.session_state.voices.keys())
                )
                st.session_state.active_voice = selected

                st.caption(
                    f"Using **{selected}** (intensity {st.session_state.voices[selected]['intensity']})"
                )

# ============================================================
# FOOTER
# ============================================================
st.caption("Olivetti — AI Write v1 (voice-aware, desk-safe)")
