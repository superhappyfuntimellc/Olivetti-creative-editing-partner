import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="🫒 Olivetti",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "text": "",
    "focus": False,
    "story_open": True,
    "voice_open": True,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    cols = st.columns([2, 1, 1, 1, 1])
    cols[0].markdown("## 🫒 **Olivetti**")
    cols[1].button("New Project")
    cols[2].button("Rough Draft")
    cols[3].button("First Edit")
    cols[4].button("Final Draft")

st.divider()

# ============================================================
# MAIN LAYOUT
# ============================================================
left, center, right = st.columns([1.3, 3.4, 1.3], gap="large")

# ============================================================
# LEFT SIDEBAR — STORY BIBLE
# ============================================================
with left:
    with st.expander("📖 Story Bible", expanded=st.session_state.story_open):
        st.text_area("Junk Drawer", height=80, key="junk")
        st.text_area("Synopsis", height=80, key="synopsis")
        st.selectbox("Genre / Style", ["Literary", "Noir", "Thriller", "Comedy"], key="genre")
        st.text_area("World Elements", height=80, key="world")
        st.text_area("Characters", height=80, key="characters")
        st.text_area("Outline (Chapters)", height=120, key="outline")

# ============================================================
# CENTER — WRITING DESK (ALWAYS VISIBLE)
# ============================================================
with center:
    st.markdown("### ✍️ Writing Desk")

    st.session_state.text = st.text_area(
        "",
        value=st.session_state.text,
        height=520,
        key="main_text"
    )

    # ---------------- BOTTOM BAR 1 ----------------
    b1 = st.columns(5)
    b1[0].button("Write")
    b1[1].button("Rewrite")
    b1[2].button("Expand")
    b1[3].button("Rephrase")
    b1[4].button("Describe")

    # ---------------- BOTTOM BAR 2 ----------------
    b2 = st.columns(5)
    b2[0].button("Spell Check")
    b2[1].button("Grammar Check")
    b2[2].button("Find / Replace")
    b2[3].button("Synonyms")
    b2[4].button("Sentence Improve")

# ============================================================
# RIGHT SIDEBAR — VOICE BIBLE
# ============================================================
with right:
    with st.expander("🎭 Voice Bible", expanded=st.session_state.voice_open):
        st.selectbox("Writing Style", ["Neutral", "Minimal", "Expressive"], key="style")
        st.selectbox("Genre Voice", ["Literary", "Hardboiled", "Poetic"], key="voice")
        st.selectbox("Trained Voices", ["— None —"], key="trained")
        st.text_area("Match My Style (Sample)", height=80, key="sample")
        st.slider("Intensity", 0.0, 1.0, 0.5, key="intensity")
        st.toggle("Voice Lock", key="voice_lock")

# ============================================================
# FOCUS MODE (HARD LOCK)
# ============================================================
if st.session_state.focus:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] { display: none; }
        </style>
        """,
        unsafe_allow_html=True
    )

# ============================================================
# FOOTER
# ============================================================
st.divider()
foot = st.columns([1, 1])
foot[0].button("🔒 Focus Mode", on_click=lambda: st.session_state.update({"focus": True}))
foot[1].caption("Olivetti — Digital Writing Desk")
