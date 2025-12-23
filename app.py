import streamlit as st
import re
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 22.2")
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
# DATA
# ============================================================
def make_story_bible():
    return {"voice_profile": "", "strength_report": ""}

def make_chapter(title, text):
    return {"title": title, "text": text, "outline": ""}

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(make_chapter(parts[i].title(), parts[i + 1].strip()))
    if not chapters:
        chapters.append(make_chapter("Chapter 1", text))
    return chapters

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
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": make_story_bible()
            }
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

# ============================================================
# MAIN GUARD
# ============================================================
if not st.session_state.current_project:
    st.title("🫒 Olivetti 22.2")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

left, center, right = st.columns([1.2, 3.2, 2.4])

# ============================================================
# LEFT — PROJECT FOLDER (REORDER CHAPTERS)
# ============================================================
with left:
    st.subheader("📁 Project Chapters")

    for i, ch in enumerate(chapters):
        cols = st.columns([6, 1, 1])
        if cols[0].button(f"{i+1}. {ch['title']}", key=f"chap_sel_{i}"):
            st.session_state.current_chapter = i
        if cols[1].button("↑", key=f"up_{i}") and i > 0:
            chapters[i - 1], chapters[i] = chapters[i], chapters[i - 1]
            st.session_state.current_chapter = i - 1
            st.experimental_rerun()
        if cols[2].button("↓", key=f"down_{i}") and i < len(chapters) - 1:
            chapters[i + 1], chapters[i] = chapters[i], chapters[i + 1]
            st.session_state.current_chapter = i + 1
            st.experimental_rerun()

    st.divider()
    move_to = st.number_input(
        "Move current chapter to position",
        min_value=1,
        max_value=len(chapters),
        value=st.session_state.current_chapter + 1
    )
    if st.button("Move Chapter"):
        idx = st.session_state.current_chapter
        ch = chapters.pop(idx)
        chapters.insert(move_to - 1, ch)
        st.session_state.current_chapter = move_to - 1
        st.experimental_rerun()

# ============================================================
# CENTER — MANUSCRIPT
# ============================================================
chapter = chapters[st.session_state.current_chapter]

with center:
    st.subheader(chapter["title"])
    chapter["text"] = st.text_area("Chapter Text", chapter["text"], height=520)

# ============================================================
# RIGHT — OUTLINE (REORDER SCENES / BEATS)
# ============================================================
with right:
    st.subheader("📑 Chapter Outline")

    if not chapter["outline"]:
        chapter["outline"] = "- Scene 1\n- Scene 2\n- Scene 3"

    beats = [b for b in chapter["outline"].splitlines() if b.strip()]

    for i, beat in enumerate(beats):
        cols = st.columns([6, 1, 1])
        cols[0].write(beat)
        if cols[1].button("↑", key=f"beat_up_{i}") and i > 0:
            beats[i - 1], beats[i] = beats[i], beats[i - 1]
            chapter["outline"] = "\n".join(beats)
            st.experimental_rerun()
        if cols[2].button("↓", key=f"beat_down_{i}") and i < len(beats) - 1:
            beats[i + 1], beats[i] = beats[i], beats[i + 1]
            chapter["outline"] = "\n".join(beats)
            st.experimental_rerun()

    st.divider()
    chapter["outline"] = st.text_area(
        "Edit Outline Manually",
        chapter["outline"],
        height=200
    )

st.caption("Olivetti 22.2 — Structural Control Without Fragility")
