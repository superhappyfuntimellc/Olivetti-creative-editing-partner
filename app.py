import streamlit as st
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="🫒 Olivetti",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE
# ============================================================
if "text" not in st.session_state:
    st.session_state.text = ""

if "focus" not in st.session_state:
    st.session_state.focus = False

if "last_saved" not in st.session_state:
    st.session_state.last_saved = None

# autosave timestamp
def autosave():
    st.session_state.last_saved = datetime.now().strftime("%H:%M:%S")

# ============================================================
# TOP BAR — MODES
# ============================================================
top = st.container()
with top:
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
    left, center, right = st.columns([1.2, 3.6, 1.2])

# ============================================================
# LEFT SIDEBAR — STORY BIBLE (COLLAPSIBLE)
# ============================================================
if left:
    with left:
        with st.expander("📖 Story Bible", expanded=False):
            st.text_area("Characters", height=120)
            st.text_area("World / Setting", height=120)
            st.text_area("Plot Threads", height=120)

# ============================================================
# CENTER — TYPE SCREEN (ALWAYS VISIBLE)
# ============================================================
with center:
    st.subheader("🫒 Writing Desk")

    st.session_state.text = st.text_area(
        "",
        value=st.session_state.text,
        height=420,
        placeholder="Just write. No project required.",
        on_change=autosave
    )

    if st.session_state.last_saved:
        st.caption(f"💾 Autosaved at {st.session_state.last_saved}")

    st.divider()

    # --------------------------------------------------------
    # BOTTOM BAR — WRITING ACTIONS
    # --------------------------------------------------------
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.button("✍️ Write")
    b2.button("🔁 Rewrite")
    b3.button("➕ Expand")
    b4.button("🔄 Rephrase")
    b5.button("🎨 Describe")

    # --------------------------------------------------------
    # SECOND BOTTOM BAR — EDITING TOOLS
    # --------------------------------------------------------
    e1, e2, e3, e4, e5 = st.columns(5)
    e1.button("🧹 Spell Check")
    e2.button("📐 Grammar")
    e3.button("🔍 Find & Replace")
    e4.button("📚 Synonyms")
    e5.button("🧠 Sentence Improve")

# ============================================================
# RIGHT SIDEBAR — VOICE / AI (COLLAPSIBLE)
# ============================================================
if right:
    with right:
        with st.expander("🎭 Voice & Style", expanded=False):
            st.selectbox("Genre", [
                "Literary", "Noir", "Thriller", "Comedy", "Lyrical"
            ])
            st.selectbox("Voice", [
                "Neutral", "Minimal", "Expressive", "Hardboiled", "Poetic"
            ])
            st.slider("Intensity", 0.0, 1.0, 0.5)
            st.text_area("Match My Style (sample)", height=120)

# ============================================================
# FOOTER
# ============================================================
st.caption("Olivetti — Your personal writing engine. Locked.")
