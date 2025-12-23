import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 20.6")
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

# ============================================================
# STYLE PRESETS
# ============================================================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit, lightness.",
    "Lyrical": "Rhythm, imagery, musical language."
}

POVS = ["First", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]

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
            "versions": [],
            "preview": ""
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "outline": "",
            "workflow": "Draft",
            "versions": [],
            "preview": ""
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def llm(system, prompt, temp=0.3):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Projects")

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

    st.divider()
    st.subheader("Voice Controls")

    genre = st.selectbox("Genre", list(GENRES.keys()))
    pov = st.selectbox("POV", POVS)
    tense = st.selectbox("Tense", TENSES)
    strictness = st.slider("Voice Strictness", 0.0, 1.0, 0.5)
    intensity = st.slider("Intensity", 0.0, 1.0, 0.5)
    anchor = st.text_area("Match My Style (anchor sample)", height=120)

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 20.6")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

left, center, right = st.columns([1.1, 3.2, 2.2])

# ============================================================
# LEFT — CHAPTERS
# ============================================================
with left:
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i
    chapter["title"] = st.text_input("Chapter title", chapter["title"])

# ============================================================
# CENTER — WRITING
# ============================================================
with center:
    st.subheader("Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    col1, col2 = st.columns(2)
    if col1.button("Save Version"):
        save_version(chapter)

    chapter["workflow"] = col2.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

# ============================================================
# RIGHT — TOOLS
# ============================================
