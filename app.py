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
        "main_text": "",
        "autosave_time": None,

        # Story Bible
        "junk": "",
        "synopsis": "",
        "genre_style": "",
        "world": "",
        "characters": "",
        "outline": "",

        # Voice Bible
        "voice_sample": "",
        "pov": "Close Third",
        "tense": "Past",
        "intensity": 0.5,

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
    cols[0].button("🆕 New Project", key="new_project")
    cols[1].button("✏️ Rough Draft", key="rough")
    cols[2].button("🛠 First Edit", key="edit")
    cols[3].button("✅ Final Draft", key="final")
    cols[4].markdown(
        f"<div style='text-align:right;font-size:12px;'>Autosave: {st.session_state.autosave_time or '—'}</div>",
        unsafe_allow_html=True
    )

st.divider()

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.4])

# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    st.subheader("📖 Story Bible")

    with st.expander("🗃 Junk Drawer", expanded=False):
        st.text_area("", key="junk", height=80)

    with st.expander("📝 Synopsis", expanded=False):
        st.text_area("", key="synopsis", height=100)

    with st.expander("🎭 Genre / Style", expanded=False):
        st.text_area("", key="genre_style", height=80)

    with st.expander("🌍 World Elements", expanded=False):
        st.text_area("", key="world", height=100)

    with st.expander("👤 Characters", expanded=False):
        st.text_area("", key="characters", height=120)

    with st.expander("🧱 Outline (Chapters)", expanded=False):
        st.text_area("", key="outline", height=160)

# ============================================================
# CENTER — TYPE SCREEN (ALWAYS VISIBLE)
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    st.text_area(
        "",
        key="main_text",
        height=520,
        on_change=autosave
    )

    # Bottom bar 1 — Writing actions
    b1 = st.columns(5)
    b1[0].button("Write", key="write")
    b1[1].button("Rewrite", key="rewrite")
    b1[2].button("Expand", key="expand")
    b1[3].button("Rephrase", key="rephrase")
    b1[4].button("Describe", key="describe")

    # Bottom bar 2 — Editing tools
    b2 = st.columns(5)
    b2[0].button("Spell Check", key="spell")
    b2[1].button("Grammar", key="grammar")
    b2[2].button("Find / Replace", key="find")
    b2[3].button("Synonyms", key="synonym")
    b2[4].button("Sentence Help", key="sentence")

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")

    with st.expander("🧬 Match My Voice", expanded=True):
        st.text_area(
            "Anchor Sample",
            key="voice_sample",
            height=120
        )

    st.selectbox(
        "POV",
        ["First", "Close Third", "Omniscient"],
        key="pov"
    )

    st.selectbox(
        "Tense",
        ["Past", "Present"],
        key="tense"
    )

    st.slider(
        "AI Intensity",
        0.0, 1.0,
        key="intensity"
    )

    st.divider()

    if st.button("🔒 Focus Mode", key="focus"):
        st.session_state.focus_mode = True
        st.experimental_rerun()

# ============================================================
# FOCUS MODE (HARD LOCK)
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
