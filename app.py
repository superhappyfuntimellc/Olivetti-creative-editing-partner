import streamlit as st
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti Desk",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# SESSION STATE INIT
# ============================================================
def init_state():
    defaults = {
        # Main writing
        "main_text": "",
        "autosave_time": None,

        # Story Bible
        "junk": "",
        "synopsis": "",
        "genre_style_notes": "",
        "world": "",
        "characters": "",
        "outline": "",

        # Voice Bible — toggles
        "vb_style_on": True,
        "vb_genre_on": True,
        "vb_trained_on": False,
        "vb_match_on": False,
        "vb_lock_on": False,

        # Voice Bible — selections
        "writing_style": "Neutral",
        "genre": "Literary",
        "trained_voice": "— None —",
        "voice_sample": "",
        "voice_lock_prompt": "",

        # Voice Bible — intensities
        "style_intensity": 0.6,
        "genre_intensity": 0.6,
        "trained_intensity": 0.7,
        "match_intensity": 0.8,
        "lock_intensity": 1.0,

        # POV / Tense
        "pov": "Close Third",
        "tense": "Past",

        # UI
        "focus_mode": False,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# AUTOSAVE
# ============================================================
def autosave():
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")

# ============================================================
# TOP BAR
# ============================================================
top = st.container()
with top:
    cols = st.columns([1, 1, 1, 1, 2])
    cols[0].button("🆕 New", key="new_project")
    cols[1].button("✏️ Rough", key="rough")
    cols[2].button("🛠 Edit", key="edit")
    cols[3].button("✅ Final", key="final")
    cols[4].markdown(
        f"<div style='text-align:right;font-size:12px;'>Autosave: {st.session_state.autosave_time or '—'}</div>",
        unsafe_allow_html=True
    )

st.divider()

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.6])

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    st.subheader("📖 Story Bible")

    with st.expander("🗃 Junk Drawer"):
        st.text_area("", key="junk", height=80)

    with st.expander("📝 Synopsis"):
        st.text_area("", key="synopsis", height=100)

    with st.expander("🎭 Genre / Style Notes"):
        st.text_area("", key="genre_style_notes", height=80)

    with st.expander("🌍 World Elements"):
        st.text_area("", key="world", height=100)

    with st.expander("👤 Characters"):
        st.text_area("", key="characters", height=120)

    with st.expander("🧱 Outline"):
        st.text_area("", key="outline", height=160)

# ============================================================
# CENTER — TYPE SCREEN (ALWAYS ON)
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    st.text_area(
        "",
        key="main_text",
        height=520,
        on_change=autosave
    )

    # Bottom bar — writing
    b1 = st.columns(5)
    b1[0].button("Write")
    b1[1].button("Rewrite")
    b1[2].button("Expand")
    b1[3].button("Rephrase")
    b1[4].button("Describe")

    # Bottom bar — editing
    b2 = st.columns(5)
    b2[0].button("Spell")
    b2[1].button("Grammar")
    b2[2].button("Find")
    b2[3].button("Synonym")
    b2[4].button("Sentence")

# ============================================================
# RIGHT — VOICE BIBLE (TOP → BOTTOM, EXACT)
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")

    # 1. Writing Style
    st.checkbox("Enable Writing Style", key="vb_style_on")
    st.selectbox(
        "Writing Style",
        ["Neutral", "Minimal", "Expressive", "Hardboiled", "Poetic"],
        key="writing_style",
        disabled=not st.session_state.vb_style_on
    )
    st.slider(
        "Style Intensity",
        0.0, 1.0,
        key="style_intensity",
        disabled=not st.session_state.vb_style_on
    )

    st.divider()

    # 2. Genre
    st.checkbox("Enable Genre Influence", key="vb_genre_on")
    st.selectbox(
        "Genre",
        ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
        key="genre",
        disabled=not st.session_state.vb_genre_on
    )
    st.slider(
        "Genre Intensity",
        0.0, 1.0,
        key="genre_intensity",
        disabled=not st.session_state.vb_genre_on
    )

    st.divider()

    # 3. Trained Voices
    st.checkbox("Enable Trained Voice", key="vb_trained_on")
    st.selectbox(
        "Trained Voice",
        ["— None —", "Voice A", "Voice B"],
        key="trained_voice",
        disabled=not st.session_state.vb_trained_on
    )
    st.slider(
        "Trained Voice Intensity",
        0.0, 1.0,
        key="trained_intensity",
        disabled=not st.session_state.vb_trained_on
    )

    st.divider()

    # 4. Match My Style
    st.checkbox("Enable Match My Style", key="vb_match_on")
    st.text_area(
        "Style Example",
        key="voice_sample",
        height=100,
        disabled=not st.session_state.vb_match_on
    )
    st.slider(
        "Match Intensity",
        0.0, 1.0,
        key="match_intensity",
        disabled=not st.session_state.vb_match_on
    )

    st.divider()

    # 5. Voice Lock
    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on")
    st.text_area(
        "Voice Lock Prompt",
        key="voice_lock_prompt",
        height=80,
        disabled=not st.session_state.vb_lock_on
    )
    st.slider(
        "Lock Strength",
        0.0, 1.0,
        key="lock_intensity",
        disabled=not st.session_state.vb_lock_on
    )

    st.divider()

    # POV / Tense
    st.selectbox("POV", ["First", "Close Third", "Omniscient"], key="pov")
    st.selectbox("Tense", ["Past", "Present"], key="tense")

    if st.button("🔒 Focus Mode"):
        st.session_state.focus_mode = True
        st.experimental_rerun()

# ============================================================
# FOCUS MODE — HARD LOCK
# ============================================================
if st.session_state.focus_mode:
    st.markdown(
        """
        <style>
        header, footer, aside, .stSidebar {display:none !important;}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.info("Focus Mode enabled. Refresh page to exit.")
