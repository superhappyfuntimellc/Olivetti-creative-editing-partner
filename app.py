import streamlit as st
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="🫒 Olivetti", layout="wide")

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
# TOP BAR
# ============================================================
c1, c2, c3, c4, c5 = st.columns([1,1,1,1,2])
with c1: st.button("🆕 New Project")
with c2: st.button("📝 Rough Draft")
with c3: st.button("✏️ First Edit")
with c4: st.button("✅ Final Draft")
with c5:
    if st.button("🎯 Focus Mode"):
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
# CENTER — TYPE SCREEN (LOCKED)
# ============================================================
with center:
    st.subheader("🫒 Writing Desk")

    st.session_state.text = st.text_area(
        "",
        st.session_state.text,
        height=420,
        placeholder="Just write. No project required.",
        on_change=autosave
    )

    if st.session_state.last_saved:
        st.caption(f"💾 Autosaved at {st.session_state.last_saved}")

    st.divider()

    b1, b2, b3, b4, b5 = st.columns(5)
    b1.button("✍️ Write")
    b2.button("🔁 Rewrite")
    b3.button("➕ Expand")
    b4.button("🔄 Rephrase")
    b5.button("🎨 Describe")

    e1, e2, e3, e4, e5 = st.columns(5)
    e1.button("🧹 Spell")
    e2.button("📐 Grammar")
    e3.button("🔍 Find")
    e4.button("📚 Synonym")
    e5.button("🧠 Sentence")

# ============================================================
# RIGHT — VOICE SYSTEM
# ============================================================
if right:
    with right:
        with st.expander("🎭 Voice Bible", expanded=True):

            voice_name = st.text_input("Voice Name")

            voice_sample = st.text_area(
                "Training Sample (paste your best paragraph)",
                height=120
            )

            intensity = st.slider("Voice Intensity", 0.0, 1.0, 0.5)

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
                    f"Using voice: **{selected}** "
                    f"(intensity {st.session_state.voices[selected]['intensity']})"
                )

            st.divider()
            st.caption("Voice affects all AI actions (next step).")

# ============================================================
# FOOTER
# ============================================================
st.caption("Olivetti — Voice system locked. Desk preserved.")
