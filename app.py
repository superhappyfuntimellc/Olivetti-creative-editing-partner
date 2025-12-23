import streamlit as st

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="🫒 Olivetti Desk",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "main_text": "",
    "focus_mode": False,
    "show_story_bible": True,
    "show_voice_bible": True,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    cols = st.columns([1,1,1,1,6])
    cols[0].button("New Project")
    cols[1].button("Rough Draft")
    cols[2].button("First Edit")
    cols[3].button("Final Draft")
    cols[4].markdown("")

st.divider()

# ============================================================
# MAIN LAYOUT
# ============================================================
left, center, right = st.columns([1.2, 4.6, 1.2])

# ============================================================
# LEFT SIDEBAR — STORY BIBLE
# ============================================================
with left:
    st.checkbox("📖 Story Bible", key="show_story_bible")

    if st.session_state.show_story_bible:
        st.subheader("Story Bible")

        st.text_area("Junk Drawer", height=80, key="sb_junk")
        st.text_area("Synopsis", height=80, key="sb_synopsis")
        st.text_input("Genre / Style", key="sb_genre")
        st.text_area("World Elements", height=80, key="sb_world")
        st.text_area("Characters", height=80, key="sb_characters")

        st.markdown("**Outline**")
        for i in range(1, 6):
            st.text_input(f"Chapter {i}", key=f"sb_chapter_{i}")

# ============================================================
# CENTER — TYPEWRITER DESK (ALWAYS ON)
# ============================================================
with center:
    st.subheader("")

    st.text_area(
        "",
        key="main_text",
        height=520,
        placeholder="Start typing. No project required."
    )

    st.divider()

    # Bottom Toolbars
    row1 = st.columns(5)
    row1[0].button("Write")
    row1[1].button("Rewrite")
    row1[2].button("Expand")
    row1[3].button("Rephrase")
    row1[4].button("Describe")

    row2 = st.columns(5)
    row2[0].button("Spell Check")
    row2[1].button("Grammar Check")
    row2[2].button("Find & Replace")
    row2[3].button("Synonym Suggest")
    row2[4].button("Sentence Suggest")

# ============================================================
# RIGHT SIDEBAR — VOICE BIBLE
# ============================================================
with right:
    st.checkbox("🎙 Voice Bible", key="show_voice_bible")

    if st.session_state.show_voice_bible:
        st.subheader("Voice Bible")

        st.selectbox(
            "Writing Style",
            ["Neutral", "Minimal", "Expressive", "Poetic", "Hardboiled"],
            key="vb_style"
        )

        st.selectbox(
            "Genre",
            ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
            key="vb_genre"
        )

        st.selectbox(
            "Trained Voices",
            ["(none yet)"],
            key="vb_trained"
        )

        st.text_area(
            "Match My Style (example)",
            height=80,
            key="vb_example"
        )

        st.selectbox(
            "Voice Lock",
            ["Unlocked", "Locked"],
            key="vb_lock"
        )

        st.slider("Intensity", 0.0, 1.0, 0.5, key="vb_intensity")

# ============================================================
# FOOTER
# ============================================================
st.caption("Olivetti Desk — Layout Locked. Intelligence Next.")
