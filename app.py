import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config("Olivetti", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    if "projects" not in st.session_state:
        st.session_state.projects = {}
    if "current_project" not in st.session_state:
        st.session_state.current_project = None
    if "current_chapter" not in st.session_state:
        st.session_state.current_chapter = 0
    if "author" not in st.session_state:
        st.session_state.author = {
            "genre": "Literary",
            "pov": "Close Third",
            "tense": "Past",
            "intensity": 0.5,
        }

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
            "text": parts[i + 1].strip(),
            "outline": "",
            "versions": [],
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "outline": "",
            "versions": [],
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def safe_chapter_access():
    project = st.session_state.projects[st.session_state.current_project]
    chapters = project["chapters"]
    st.session_state.current_chapter = max(
        0, min(st.session_state.current_chapter, len(chapters) - 1)
    )
    return project, chapters, chapters[st.session_state.current_chapter]

def llm(system, prompt, temp):
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
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("Projects")
    names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + names)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {
                "chapters": [],
                "story_bible": "",
                "voice_anchor": ""
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
            st.session_state.current_chapter = 0

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("🫒 Olivetti")
    st.stop()

project, chapters, chapter = safe_chapter_access()

# ============================================================
# AUTHOR CONTROLS (GLOBAL)
# ============================================================
top = st.columns(4)
top[0].selectbox("Genre", ["Literary","Noir","Thriller","Comedy","Lyrical"], key="author.genre")
top[1].selectbox("POV", ["First","Close Third","Omniscient"], key="author.pov")
top[2].selectbox("Tense", ["Past","Present"], key="author.tense")
top[3].slider("Intensity", 0.0, 1.0, key="author.intensity")

st.divider()

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.2, 3.4, 2])

# ---------------- LEFT — STRUCTURE ----------------
with left:
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        cols = st.columns([6,1,1])
        if cols[0].button(f"{i+1}. {ch['title']}", key=f"sel{i}"):
            st.session_state.current_chapter = i
        if cols[1].button("↑", key=f"up{i}") and i > 0:
            chapters[i-1], chapters[i] = chapters[i], chapters[i-1]
        if cols[2].button("↓", key=f"dn{i}") and i < len(chapters)-1:
            chapters[i+1], chapters[i] = chapters[i], chapters[i+1]

# ---------------- CENTER — WRITING ----------------
with center:
    chapter["title"] = st.text_input("Chapter title", chapter["title"])
    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=560,
        key=f"autosave_{st.session_state.current_chapter}"
    )

    if st.button("Save Version"):
        save_version(chapter)

# ---------------- RIGHT — AI TOOLS ----------------
with right:
    st.subheader("AI Tools")

    if st.button("Tighten"):
        chapter["text"] = llm(
            "You are a line editor.",
            f"Tighten this prose without changing meaning:\n{chapter['text']}",
            0.3
        )

    if st.button("Expand"):
        chapter["text"] = llm(
            "You are a fiction writer.",
            f"Expand this scene with richer detail:\n{chapter['text']}",
            0.6
        )

    if st.button("Sharpen Voice"):
        chapter["text"] = llm(
            "You are refining authorial voice.",
            f"Sharpen the voice while keeping POV and tense:\n{chapter['text']}",
            0.5
        )

    st.divider()
    st.subheader("Voice Trainer")

    project["voice_anchor"] = st.text_area(
        "Anchor sample (your best writing)",
        project.get("voice_anchor",""),
        height=120
    )

# ============================================================
# STORY BIBLE
# ============================================================
st.divider()
st.subheader("Story Bible")
project["story_bible"] = st.text_area(
    "",
    project["story_bible"],
    height=240
)

st.caption("Olivetti 25.0 — Stable, Powerful, Yours")
