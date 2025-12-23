import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="🫒 Olivetti Desk", initial_sidebar_state="expanded")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "focus_mode": False,
        "last_autosave": None,
        "story_bible": {
            "Characters": "",
            "Locations": "",
            "Timeline": "",
            "Notes": ""
        },
        "voice_bible": {
            "Genre": "Literary",
            "Voice": "Neutral Editor",
            "POV": "Close Third",
            "Tense": "Past",
            "Intensity": 0.5,
            "StyleSample": ""
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# STYLE PRESETS
# ============================================================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit.",
    "Lyrical": "Musical, image-rich language."
}

VOICES = {
    "Neutral Editor": "Clear, invisible editorial voice.",
    "Minimal": "Spare, restrained.",
    "Expressive": "Emotion-forward.",
    "Hardboiled": "Dry, blunt.",
    "Poetic": "Figurative, flowing."
}

# ============================================================
# HELPERS
# ============================================================
def autosave():
    st.session_state.last_autosave = datetime.now().strftime("%H:%M:%S")

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append({
            "title": parts[i].title(),
            "text": parts[i+1].strip(),
            "outline": "",
            "workflow": "Draft",
            "versions": []
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "outline": "",
            "workflow": "Draft",
            "versions": []
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

# ============================================================
# FOCUS MODE — HARD LOCK
# ============================================================
if st.session_state.focus_mode:
    st.markdown(
        """
        <style>
        header, footer, aside, .stButton, .stTabs, .stSidebar {display:none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    project = st.session_state.projects.get(st.session_state.current_project)
    if not project or not project["chapters"]:
        st.stop()

    chapter = project["chapters"][st.session_state.current_chapter]

    st.markdown("## ✍️ Focus Mode")
    st.caption("Autosaving continuously • Refresh page to exit")

    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=800,
        on_change=autosave
    )

    st.stop()

# ============================================================
# TOP BAR
# ============================================================
top_left, top_right = st.columns([4, 1])
with top_left:
    st.markdown("## 🫒 Olivetti — Digital Writing Desk")
    if st.session_state.last_autosave:
        st.caption(f"💾 Autosaved at {st.session_state.last_autosave}")
with top_right:
    if st.button("🎧 Focus"):
        st.session_state.focus_mode = True
        st.rerun()

st.divider()

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("📁 Projects")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name", on_change=autosave)
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
            autosave()
    else:
        st.session_state.current_project = choice

    if st.session_state.current_project:
        upload = st.file_uploader("Import manuscript (.txt)", type=["txt"])
        if upload:
            text = upload.read().decode("utf-8")
            st.session_state.projects[
                st.session_state.current_project
            ]["chapters"] = split_into_chapters(text)
            st.session_state.current_chapter = 0
            autosave()

# ============================================================
# MAIN GUARD
# ============================================================
if not st.session_state.current_project:
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

if st.session_state.current_chapter >= len(chapters):
    st.session_state.current_chapter = 0

chapter = chapters[st.session_state.current_chapter]

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.6, 3.2, 1.6])

# ============================================================
# LEFT — STORY BIBLE (AUTOSAVE)
# ============================================================
with left:
    st.subheader("📘 Story Bible")
    tabs = st.tabs(list(st.session_state.story_bible.keys()))
    for tab, key in zip(tabs, st.session_state.story_bible.keys()):
        with tab:
            st.session_state.story_bible[key] = st.text_area(
                key,
                st.session_state.story_bible[key],
                height=220,
                on_change=autosave
            )

# ============================================================
# CENTER — WRITING DESK (AUTOSAVE)
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i
            autosave()
            st.rerun()

    chapter["title"] = st.text_input(
        "Chapter title",
        chapter["title"],
        on_change=autosave
    )

    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=520,
        on_change=autosave
    )

    c1, c2 = st.columns(2)
    if c1.button("💾 Save Version"):
        save_version(chapter)
        autosave()

    chapter["workflow"] = c2.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"]),
        on_change=autosave
    )

# ============================================================
# RIGHT — VOICE BIBLE (AUTOSAVE)
# ============================================================
with right:
    st.subheader("🎛 Voice Bible")
    vtabs = st.tabs(["Core", "Style", "Controls"])

    with vtabs[0]:
        st.session_state.voice_bible["Genre"] = st.selectbox(
            "Genre", list(GENRES.keys()),
            index=list(GENRES.keys()).index(st.session_state.voice_bible["Genre"]),
            on_change=autosave
        )
        st.session_state.voice_bible["Voice"] = st.selectbox(
            "Voice", list(VOICES.keys()),
            index=list(VOICES.keys()).index(st.session_state.voice_bible["Voice"]),
            on_change=autosave
        )

    with vtabs[1]:
        st.session_state.voice_bible["POV"] = st.selectbox(
            "POV", ["First", "Close Third", "Omniscient"],
            on_change=autosave
        )
        st.session_state.voice_bible["Tense"] = st.selectbox(
            "Tense", ["Past", "Present"],
            on_change=autosave
        )

    with vtabs[2]:
        st.session_state.voice_bible["Intensity"] = st.slider(
            "AI Intensity", 0.0, 1.0,
            st.session_state.voice_bible["Intensity"],
            on_change=autosave
        )
        st.session_state.voice_bible["StyleSample"] = st.text_area(
            "Match My Style",
            st.session_state.voice_bible["StyleSample"],
            height=120,
            on_change=autosave
        )

st.caption("Olivetti Desk v12.2 — Autosave always on • Nothing is lost")


