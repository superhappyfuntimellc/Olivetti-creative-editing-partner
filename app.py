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
# SESSION STATE (AUTOSAVE CORE)
# ============================================================
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
    "trained": "— None —",
    "sample": "",
    "intensity": 0.5,
    "voice_lock": False,
    "focus": False,
}

for key, value in STATE_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ============================================================
# TOP BAR
# ============================================================
with st.container():
    cols = st.columns([2, 1, 1, 1, 1])
    cols[0].markdown("## 🫒 **Olivetti**")
    cols[1].button("New Project", key="top_new")
    cols[2].button("Rough Draft", key="top_rough")
    cols[3].button("First Edit", key="top_edit")
    cols[4].button("Final Draft", key="top_final")

st.divider()

# ============================================================
# MAIN LAYOUT
# ============================================================
left, center, right = st.columns([1.3, 3.4, 1.3], gap="large")

# ============================================================
# LEFT — STORY BIBLE (AUTOSAVED)
# ============================================================
with left:
    with st.expander("📖 Story Bible", expanded=True):
        st.text_area("Junk Drawer", key="junk", height=80)
        st.text_area("Synopsis", key="synopsis", height=80)
        st.selectbox(
            "Genre / Style",
            ["Literary", "Noir", "Thriller", "Comedy"],
            key="genre"
        )
        st.text_area("World Elements", key="world", height=80)
        st.text_area("Characters", key="characters", height=80)
        st.text_area("Outline (Chapters)", key="outline", height=120)

# ============================================================
# CENTER — WRITING DESK (ALWAYS ON, AUTOSAVED)
# ============================================================
with center:
    st.markdown("### ✍️ Writing Desk")

    st.text_area(
        "",
        key="text",
        height=540
    )

    # -------- Bottom Bar 1 --------
    bar1 = st.columns(5)
    bar1[0].button("Write", key="write")
    bar1[1].button("Rewrite", key="rewrite")
    bar1[2].button("Expand", key="expand")
    bar1[3].button("Rephrase", key="rephrase")
    bar1[4].button("Describe", key="describe")

    # -------- Bottom Bar 2 --------
    bar2 = st.columns(5)
    bar2[0].button("Spell Check", key="spell")
    bar2[1].button("Grammar Check", key="grammar")
    bar2[2].button("Find / Replace", key="find")
    bar2[3].button("Synonyms", key="syn")
    bar2[4].button("Sentence Improve", key="sentence")

# ============================================================
# RIGHT — VOICE BIBLE (AUTOSAVED)
# ============================================================
with right:
    with st.expander("🎭 Voice Bible", expanded=True):
        st.selectbox(
            "Writing Style",
            ["Neutral", "Minimal", "Expressive"],
            key="style"
        )
        st.selectbox(
            "Genre Voice",
            ["Literary", "Hardboiled", "Poetic"],
            key="voice"
        )
        st.selectbox(
            "Trained Voices",
            ["— None —"],
            key="trained"
        )
        st.text_area(
            "Match My Style (Sample)",
            key="sample",
            height=80
        )
        st.slider(
            "Intensity",
            0.0,
            1.0,
            key="intensity"
        )
        st.toggle(
            "Voice Lock",
            key="voice_lock"
        )

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
footer = st.columns([1, 1])
footer[0].button(
    "🔒 Focus Mode",
    key="focus_btn",
    on_click=lambda: st.session_state.update({"focus": True})
)
footer[1].caption("Olivetti — Digital Writing Desk")
