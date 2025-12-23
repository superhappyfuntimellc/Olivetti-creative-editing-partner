import streamlit as st

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti – Voice Bible Hardened",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE INITIALIZATION (DEFENSIVE)
# ============================================================
def init_state(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

# UI state
init_state("show_left", True)
init_state("show_right", True)

# Writing desk
init_state("free_write", "")

# Voice Bible state
VOICE_BLOCKS = [
    "writing_style",
    "genre",
    "trained_voice",
    "match_style",
    "voice_lock"
]

for block in VOICE_BLOCKS:
    init_state(f"{block}_enabled", True)
    init_state(f"{block}_intensity", 0.5)
    init_state(f"{block}_value", "")

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    c1, c2, c3 = st.columns([1, 6, 1])
    with c1:
        if st.button("☰ Left", key="toggle_left"):
            st.session_state.show_left = not st.session_state.show_left
    with c2:
        st.markdown("### 🫒 Olivetti — Writing Desk")
    with c3:
        if st.button("☰ Right", key="toggle_right"):
            st.session_state.show_right = not st.session_state.show_right

# ============================================================
# MAIN LAYOUT
# ============================================================
left_col, center_col, right_col = st.columns([1.4, 4.2, 1.8])

# ============================================================
# LEFT SIDEBAR (PLACEHOLDER – LOCKED, NOT MODIFIED)
# ============================================================
with left_col:
    if st.session_state.show_left:
        st.subheader("📖 Story Bible")
        st.text_area(
            "Notes",
            height=200,
            key="story_notes"
        )

# ============================================================
# CENTER WRITING DESK (SACRED)
# ============================================================
with center_col:
    st.subheader("✍️ Writing Desk")
    st.text_area(
        "",
        height=600,
        key="free_write"
    )

# ============================================================
# RIGHT SIDEBAR — VOICE BIBLE (NORMALIZED)
# ============================================================
with right_col:
    if st.session_state.show_right:
        st.subheader("🎙 Voice Bible")

        def voice_block(block_id, label, widget_fn):
            st.markdown("---")
            cols = st.columns([1, 2, 3])
            with cols[0]:
                st.checkbox(
                    "ON",
                    key=f"{block_id}_enabled"
                )
            with cols[1]:
                st.slider(
                    "Intensity",
                    0.0,
                    1.0,
                    key=f"{block_id}_intensity"
                )
            with cols[2]:
                widget_fn()

        # Writing Style
        voice_block(
            "writing_style",
            "Writing Style",
            lambda: st.selectbox(
                "Writing Style",
                ["Neutral", "Minimal", "Expressive", "Poetic"],
                key="writing_style_value"
            )
        )

        # Genre
        voice_block(
            "genre",
            "Genre",
            lambda: st.selectbox(
                "Genre",
                ["Literary", "Noir", "Thriller", "Lyrical"],
                key="genre_value"
            )
        )

        # Trained Voice
        voice_block(
            "trained_voice",
            "Trained Voice",
            lambda: st.selectbox(
                "Trained Voice",
                ["Default", "Voice A", "Voice B"],
                key="trained_voice_value"
            )
        )

        # Match My Style
        voice_block(
            "match_style",
            "Match My Style",
            lambda: st.text_area(
                "Style Sample",
                height=120,
                key="match_style_value"
            )
        )

        # Voice Lock
        voice_block(
            "voice_lock",
            "Voice Lock",
            lambda: st.text_input(
                "Lock Prompt",
                key="voice_lock_value"
            )
        )

# ============================================================
# FOOTER (DEBUG SAFE)
# ============================================================
st.caption("Olivetti — Voice Bible normalized, stable, professional-grade")
