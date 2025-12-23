import streamlit as st
import re
from datetime import datetime
from typing import List, Dict

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Olivetti 24.0",
    layout="wide",
    initial_sidebar_state="expanded",
)
# =========================
# ITALIAN MODERN DESK SKIN
# =========================
st.markdown("""
<style>

/* --- Global --- */
html, body, [class*="css"] {
    font-family: "IBM Plex Serif", "Georgia", serif;
    background-color: #f6f1eb;
    color: #2b2b2b;
}

/* --- Main writing surface --- */
textarea {
    background-color: #fbf9f6 !important;
    border: 1px solid #d8d2cb !important;
    border-radius: 10px !important;
    padding: 16px !important;
    font-size: 1.05rem !important;
    line-height: 1.6 !important;
}

/* --- Inputs & Selects --- */
input, select {
    background-color: #fbf9f6 !important;
    border-radius: 8px !important;
    border: 1px solid #d8d2cb !important;
}

/* --- Buttons --- */
button {
    background-color: #ece6df !important;
    color: #2b2b2b !important;
    border-radius: 8px !important;
    border: 1px solid #d0c7bd !important;
    font-weight: 500 !important;
}

button:hover {
    background-color: #e0d7ce !important;
}

/* --- Accent (Olivetti red) --- */
div[data-baseweb="slider"] > div {
    color: #b22222;
}

/* --- Sidebar --- */
section[data-testid="stSidebar"] {
    background-color: #efe9e2;
    border-right: 1px solid #d6cdc3;
}

/* --- Headers --- */
h1, h2, h3 {
    font-weight: 500;
    letter-spacing: 0.3px;
}

/* --- Focus Mode Calm --- */
body:has(input[type="checkbox"]:checked) textarea {
    background-color: #fffdfb !important;
    box-shadow: 0 0 0 1px #e6dfd7;
}

/* --- Reduce visual noise --- */
hr {
    border: none;
    border-top: 1px solid #ddd4cb;
}

/* --- Caption --- */
footer {
    opacity: 0.6;
}

</style>
""", unsafe_allow_html=True)

# =========================
# OPTIONAL LOCAL DRAG SUPPORT
# =========================
DRAG_AVAILABLE = False
try:
    from streamlit_sortables import sort_items
    DRAG_AVAILABLE = True
except Exception:
    DRAG_AVAILABLE = False

# =========================
# SESSION STATE INIT
# =========================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "focus_mode": False,
        "pov": "Close Third",
        "tense": "Past",
        "intensity": 0.5,
        "voice_bible": "",
        "voice_locked": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================
# STYLE PRESETS
# =========================
POVS = ["First", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]

# =========================
# HELPERS
# =========================
def safe_index(lst: list, idx: int):
    if not lst:
        return None
    return lst[min(max(idx, 0), len(lst) - 1)]

def split_into_chapters(text: str) -> List[Dict]:
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append({
            "title": parts[i].title(),
            "text": parts[i + 1].strip(),
            "outline": "",
            "workflow": "Draft",
            "versions": [],
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text.strip(),
            "outline": "",
            "workflow": "Draft",
            "versions": [],
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"],
    })

# =========================
# AI DISPATCHER (MID PROFILE)
# =========================
def ai_stub(action: str, text: str) -> str:
    """
    Replace internals with OpenAI calls.
    This stub keeps the app stable.
    """
    header = f"[AI: {action} | POV={st.session_state.pov} | Tense={st.session_state.tense} | Intensity={st.session_state.intensity:.2f}]"
    return f"{header}\n\n{text}"

# =========================
# TOP BAR (ALWAYS VISIBLE)
# =========================
with st.container():
    top = st.columns([2, 1, 1, 2, 1, 1])
    with top[0]:
        st.markdown("### Olivetti 24.0")
    with top[1]:
        st.session_state.pov = st.selectbox("POV", POVS, index=POVS.index(st.session_state.pov))
    with top[2]:
        st.session_state.tense = st.selectbox("Tense", TENSES, index=TENSES.index(st.session_state.tense))
    with top[3]:
        st.session_state.intensity = st.slider("Intensity", 0.0, 1.0, st.session_state.intensity)
    with top[4]:
        st.toggle("Focus", key="focus_mode")
    with top[5]:
        st.write(" ")

st.divider()

# =========================
# SIDEBAR (ALWAYS ACCESSIBLE)
# =========================
with st.sidebar:
    st.header("Projects")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

    if st.session_state.current_project:
        upload = st.file_uploader("Import manuscript (.txt)", type=["txt"])
        if upload:
            text = upload.read().decode("utf-8")
            st.session_state.projects[st.session_state.current_project]["chapters"] = split_into_chapters(text)
            st.session_state.current_chapter = 0

    st.divider()
    st.subheader("Voice Bible")
    st.session_state.voice_bible = st.text_area(
        "Anchor voice",
        st.session_state.voice_bible,
        height=120,
        disabled=st.session_state.voice_locked,
    )
    st.session_state.voice_locked = st.checkbox("Lock Voice Bible")

# =========================
# MAIN BODY
# =========================
if not st.session_state.current_project:
    st.title("Your digital writing desk")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project.get("chapters", [])

chapter = safe_index(chapters, st.session_state.current_chapter)
if chapter is None:
    st.write("No chapters yet.")
    st.stop()

# =========================
# LAYOUT
# =========================
left, center, right = st.columns([1.1, 3.2, 2.0])

# =========================
# LEFT — CHAPTERS
# =========================
with left:
    st.subheader("Chapters")

    titles = [c["title"] for c in chapters]

    if DRAG_AVAILABLE and not st.session_state.focus_mode:
        new_order = sort_items(titles)
        if new_order != titles:
            reordered = [chapters[titles.index(t)] for t in new_order]
            project["chapters"] = reordered
            chapters = reordered
    else:
        for i, ch in enumerate(chapters):
            if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
                st.session_state.current_chapter = i

# =========================
# CENTER — WRITING SURFACE
# =========================
with center:
    st.subheader(chapter["title"])
    chapter["title"] = st.text_input("Title", chapter["title"])

    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=600 if st.session_state.focus_mode else 450,
    )

    if not st.session_state.focus_mode:
        c1, c2 = st.columns(2)
        if c1.button("Save Version"):
            save_version(chapter)
        chapter["workflow"] = c2.selectbox(
            "Workflow",
            ["Draft", "Revise", "Polish", "Final"],
            index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"]),
        )

# =========================
# RIGHT — AI TOOLS
# =========================
with right:
    if st.session_state.focus_mode:
        st.write("Focus mode active.")
    else:
        st.subheader("AI Tools")

        if st.button("Rewrite"):
            chapter["preview"] = ai_stub("Rewrite", chapter["text"])

        if st.button("Tighten"):
            chapter["preview"] = ai_stub("Tighten", chapter["text"])

        if st.button("Expand"):
            chapter["preview"] = ai_stub("Expand", chapter["text"])

        if st.button("Analyze Scene"):
            chapter["analysis"] = ai_stub("Analysis", chapter["text"])

        if "preview" in chapter:
            st.text_area("Preview", chapter["preview"], height=200)
            if st.button("Accept Rewrite"):
                save_version(chapter)
                chapter["text"] = chapter.pop("preview")

        if "analysis" in chapter:
            st.text_area("Notes", chapter["analysis"], height=160)

st.caption("Olivetti 24.0 — Balanced, stable, built to write all day")

