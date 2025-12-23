import streamlit as st
import re
from datetime import datetime
from collections import Counter
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti 23.6", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "voice_bible": {},
        "analysis": [],
        "intensity": 0.5,
        "pov": "Close Third",
        "tense": "Past",
        "structure_locked": False,
        "instruction_bible": {
            "Editorial": "Revise for clarity and flow without changing voice.",
            "Minimal": "Make the smallest possible improvement.",
            "Aggressive": "Rewrite boldly for impact.",
            "Voice Locked": "Rewrite strictly matching the author’s voice."
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

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
            "workflow": "Draft",
            "versions": []
        })

    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "workflow": "Draft",
            "versions": []
        })

    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def split_scenes(text):
    return re.split(r"\n\s*(?:---|SCENE:)\s*\n", text)

def join_scenes(scenes):
    return "\n\n---\n\n".join(scenes)

# ============================================================
# TOP BAR
# ============================================================
top = st.columns([2,2,2,2,2])
top[0].slider("Intensity", 0.0, 1.0, key="intensity")
top[1].selectbox("POV", ["First","Close Third","Omniscient"], key="pov")
top[2].selectbox("Tense", ["Past","Present"], key="tense")
top[3].toggle("🔒 Lock Structure", key="structure_locked")
top[4].button("Snapshot")

st.divider()

# ============================================================
# SIDEBAR — PROJECTS + STRUCTURE
# ============================================================
with st.sidebar:
    st.header("Projects")
    names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + names)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

    if not st.session_state.current_project:
        st.stop()

    project = st.session_state.projects[st.session_state.current_project]
    chapters = project["chapters"]

    st.divider()
    st.subheader("Chapters")

    for i, ch in enumerate(chapters):
        cols = st.columns([6,1,1])
        if cols[0].button(f"{i+1}. {ch['title']}", key=f"ch_{i}"):
            st.session_state.current_chapter = i

        if not st.session_state.structure_locked:
            if cols[1].button("↑", key=f"up_{i}") and i > 0:
                chapters[i-1], chapters[i] = chapters[i], chapters[i-1]
                st.session_state.current_chapter = i-1
            if cols[2].button("↓", key=f"dn_{i}") and i < len(chapters)-1:
                chapters[i+1], chapters[i] = chapters[i], chapters[i+1]
                st.session_state.current_chapter = i+1

# ============================================================
# MAIN — EDITOR + SCENES
# ============================================================
chapter = chapters[st.session_state.current_chapter]

left, center = st.columns([1,3])

with left:
    st.subheader("Scenes")
    scenes = split_scenes(chapter["text"])

    for i, sc in enumerate(scenes):
        cols = st.columns([6,1,1])
        cols[0].write(f"Scene {i+1}")

        if not st.session_state.structure_locked:
            if cols[1].button("↑", key=f"sc_up_{i}") and i > 0:
                scenes[i-1], scenes[i] = scenes[i], scenes[i-1]
            if cols[2].button("↓", key=f"sc_dn_{i}") and i < len(scenes)-1:
                scenes[i+1], scenes[i] = scenes[i], scenes[i+1]

    chapter["text"] = join_scenes(scenes)

with center:
    st.subheader("Chapter Text")
    chapter["title"] = st.text_input("Chapter Title", chapter["title"])
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    c1, c2 = st.columns(2)
    if c1.button("Save Version"):
        save_version(chapter)

    chapter["workflow"] = c2.selectbox(
        "Workflow",
        ["Draft","Revise","Polish","Final"],
        index=["Draft","Revise","Polish","Final"].index(chapter["workflow"])
    )

st.caption("Olivetti 23.6 — Structural Control with Lock")
