import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="🫒 Olivetti Desk")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
if "projects" not in st.session_state:
    st.session_state.projects = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

if "story_bible" not in st.session_state:
    st.session_state.story_bible = {
        "Characters": "",
        "Locations": "",
        "Timeline": "",
        "Notes": ""
    }

if "voice_bible" not in st.session_state:
    st.session_state.voice_bible = {
        "Genre": "Literary",
        "Voice": "Neutral Editor",
        "POV": "Close Third",
        "Tense": "Past",
        "Intensity": 0.5,
        "StyleSample": ""
    }

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
    "Minimal": "Spare, restrained, subtext-driven.",
    "Expressive": "Emotion-forward, vivid.",
    "Hardboiled": "Dry, blunt, unsentimental.",
    "Poetic": "Figurative, flowing."
}

# ============================================================
# HELPERS
# ============================================================
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
# TOP BAR
# ============================================================
st.markdown("## 🫒 Olivetti — Your Digital Writing Desk")
st.caption("A focused, trainable authorial engine")

st.divider()

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("📁 Projects")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
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

# Safety clamp
if st.session_state.current_chapter >= len(chapters):
    st.session_state.current_chapter = 0

chapter = chapters[st.session_state.current_chapter]

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.6, 3.2, 1.6])

# ============================================================
# LEFT — STORY BIBLE (TABS)
# ============================================================
with left:
    st.subheader("📘 Story Bible")
    tabs = st.tabs(list(st.session_state.story_bible.keys()))

    for tab, key in zip(tabs, st.session_state.story_bible.keys()):
        with tab:
            st.session_state.story_bible[key] = st.text_area(
                key,
                st.session_state.story_bible[key],
                height=220
            )

# ============================================================
# CENTER — WRITING DESK
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")

    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i
            st.rerun()

    chapter["title"] = st.text_input("Chapter title", chapter["title"])
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    c1, c2 = st.columns(2)
    if c1.button("💾 Save Version"):
        save_version(chapter)

    chapter["workflow"] = c2.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

# ============================================================
# RIGHT — VOICE BIBLE (TABS)
# ============================================================
with right:
    st.subheader("🎛 Voice Bible")
    vtabs = st.tabs(["Core", "Style", "Controls"])

    with vtabs[0]:
        st.session_state.voice_bible["Genre"] = st.selectbox(
            "Genre", list(GENRES.keys())
        )
        st.session_state.voice_bible["Voice"] = st.selectbox(
            "Voice", list(VOICES.keys())
        )

    with vtabs[1]:
        st.session_state.voice_bible["POV"] = st.selectbox(
            "POV", ["First", "Close Third", "Omniscient"]
        )
        st.session_state.voice_bible["Tense"] = st.selectbox(
            "Tense", ["Past", "Present"]
        )

    with vtabs[2]:
        st.session_state.voice_bible["Intensity"] = st.slider(
            "AI Intensity",
            0.0, 1.0,
            st.session_state.voice_bible["Intensity"]
        )
        st.session_state.voice_bible["StyleSample"] = st.text_area(
            "Match My Style",
            st.session_state.voice_bible["StyleSample"],
            height=120
        )

st.caption("Olivetti Desk v12 — stable UI restoration complete")
