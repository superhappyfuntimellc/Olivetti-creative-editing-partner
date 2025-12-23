import streamlit as st

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="🫒 Olivetti Desk",
    layout="wide",
)

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "main_text": "",
    "show_story_bible": True,
    "show_voice_bible": True,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# TOP BAR (ALWAYS VISIBLE)
# ============================================================
top = st.container()
with top:
    c = st.columns([1,1,1,1,4])
    c[0].button("New Project")
    c[1].button("Rough Draft")
    c[2].button("First Edit")
    c[3].button("Final Draft")
    c[4].markdown("")

st.divider()

# ============================================================
# COLLAPSIBLE LAYOUT LOGIC
# ============================================================
left_width  = 1.2 if st.session_state.show_story_bible else 0.05
right_width = 1.2 if st.session_state.show_voice_bible else 0.05

left, center, right = st.columns([left_width, 4.8, right_width])

# ============================================================
# LEFT SIDEBAR — STORY BIBLE
# ============================================================
with left:
    if st.button("📖 Story Bible"):
        st.session_state.show_story_bible = not st.session_state.show_story_bible

    if st.session_state.show_story_bible:
        st.markdown("### Story Bible")

        st.text_area("Junk Drawer", height=70, key="sb_junk")
        st.text_area("Synopsis", height=70, key="sb_synopsis")
        st.text_input("Genre / Style", key="sb_genre")
        st.text_area("World Elements", height=70, key="sb_world")
        st.text_area("Characters", height=70, key="sb_characters")

        st.markdown("**Outline**")
        for i in range(1, 6):
            st.text_input(f"Chapter {i}", key=f"sb_ch_{i}")

# ============================================================
# CENTER — TYPE SCREEN (ALWAYS ON)
# ============================================================
with center:
    st.text_area(
        "",
        key="main_text",
        height=560,
        placeholder="Just type. No project required."
    )

    st.divider()

    # Bottom bar — row 1
    r1 = st.columns(5)
    r1[0].button("Write")
    r1[1].button("Rewrite")
    r1[2].button("Expand")
    r1[3].button("Rephrase")
    r1[4].button("Describe")

    # Bottom bar — row 2
    r2 = st.columns(5)
    r2[0].button("Spell Check")
    r2[1].button("Grammar Check")
    r2[2].button("Find & Replace")
    r2[3].button("Synonym Suggest")
    r2[4].button("Sentence Suggest")

# ============================================================
# RIGHT SIDEBAR — VOICE BIBLE
# ============================================================
with right:
    if st.button("🎙 Voice Bible"):
        st.session_state.show_voice_bible = not st.session_state.show_voice_bible

    if st.session_state.show_voice_bible:
        st.markdown("### Voice Bible")

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

        st.slider(
            "Intensity",
            0.0, 1.0, 0.5,
            key="vb_intensity"
        )

# ============================================================
# FOOTER
# ============================================================
st.caption("Olivetti Desk — Layout locked. Behavior comes next.")
