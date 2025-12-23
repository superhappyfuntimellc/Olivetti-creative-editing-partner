import streamlit as st
import time

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
    "focus_mode": False,
    "last_save": time.time(),
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# AUTOSAVE
# ============================================================
def autosave():
    st.session_state.last_save = time.time()

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    c = st.columns([1,1,1,1,1,3])
    c[0].button("New Project")
    c[1].button("Rough Draft")
    c[2].button("First Edit")
    c[3].button("Final Draft")

    if c[4].button("🎯 Focus"):
        st.session_state.focus_mode = True

    c[5].markdown("")

st.divider()

# ============================================================
# FOCUS MODE (SAFE VERSION)
# ============================================================
if st.session_state.focus_mode:
    st.text_area(
        "",
        key="main_text",
        height=720,
        placeholder="Focus Mode active. Refresh the page to exit.",
        on_change=autosave
    )
    st.caption("Focus Mode — refresh to unlock.")
    st.stop()

# ============================================================
# COLLAPSIBLE LAYOUT
# ============================================================
left_w  = 1.2 if st.session_state.show_story_bible else 0.05
right_w = 1.2 if st.session_state.show_voice_bible else 0.05

left, center, right = st.columns([left_w, 4.8, right_w])

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    if st.button("📖 Story Bible"):
        st.session_state.show_story_bible = not st.session_state.show_story_bible

    if st.session_state.show_story_bible:
        st.markdown("### Story Bible")
        st.text_area("Junk Drawer", height=70, key="sb_junk", on_change=autosave)
        st.text_area("Synopsis", height=70, key="sb_synopsis", on_change=autosave)
        st.text_input("Genre / Style", key="sb_genre", on_change=autosave)
        st.text_area("World Elements", height=70, key="sb_world", on_change=autosave)
        st.text_area("Characters", height=70, key="sb_characters", on_change=autosave)

        st.markdown("**Outline**")
        for i in range(1, 6):
            st.text_input(f"Chapter {i}", key=f"sb_ch_{i}", on_change=autosave)

# ============================================================
# CENTER — TYPEWRITER DESK (ALWAYS ON)
# ============================================================
with center:
    st.text_area(
        "",
        key="main_text",
        height=560,
        placeholder="Just type. No project required.",
        on_change=autosave
    )

    st.divider()

    r1 = st.columns(5)
    for label, col in zip(
        ["Write","Rewrite","Expand","Rephrase","Describe"], r1
    ):
        col.button(label)

    r2 = st.columns(5)
    for label, col in zip(
        ["Spell Check","Grammar Check","Find & Replace","Synonym Suggest","Sentence Suggest"], r2
    ):
        col.button(label)

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
with right:
    if st.button("🎙 Voice Bible"):
        st.session_state.show_voice_bible = not st.session_state.show_voice_bible

    if st.session_state.show_voice_bible:
        st.markdown("### Voice Bible")
        st.selectbox("Writing Style", ["Neutral","Minimal","Expressive","Poetic","Hardboiled"], key="vb_style")
        st.selectbox("Genre", ["Literary","Noir","Thriller","Comedy","Lyrical"], key="vb_genre")
        st.selectbox("Trained Voices", ["(none yet)"], key="vb_trained")
        st.text_area("Match My Style", height=80, key="vb_example", on_change=autosave)
        st.selectbox("Voice Lock", ["Unlocked","Locked"], key="vb_lock")
        st.slider("Intensity", 0.0, 1.0, 0.5, key="vb_intensity")

# ============================================================
# FOOTER
# ============================================================
st.caption("Olivetti Desk — Stable core. Proven layout.")
