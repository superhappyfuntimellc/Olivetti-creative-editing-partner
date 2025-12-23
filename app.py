import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti",
    layout="wide",
)

client = OpenAI()

# ============================================================
# SESSION STATE — SINGLE SOURCE OF TRUTH
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "author_state": {
            "genre": "Literary",
            "pov": "Close Third",
            "tense": "Past",
            "intensity": 0.5,
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# HELPERS — SAFE, BORING, RELIABLE
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


def save_version(chapter):
    chapter["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": chapter["text"],
    })


def get_current_chapter():
    if not st.session_state.current_project:
        st.stop()

    project = st.session_state.projects.get(st.session_state.current_project)
    if not project:
        st.stop()

    chapters = project.get("chapters", [])
    if not chapters:
        st.warning("No chapters yet. Import a manuscript to begin.")
        st.stop()

    st.session_state.current_chapter = max(
        0,
        min(st.session_state.current_chapter, len(chapters) - 1)
    )

    return project, chapters, chapters[st.session_state.current_chapter]


def call_llm(system, prompt, temperature):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return r.output_text


def generate_outline(text):
    a = st.session_state.author_state
    prompt = f"""
Create a concise chapter outline.

Rules:
- Bullet points only
- Major beats only
- No rewriting

Style:
Genre: {a['genre']}
POV: {a['pov']}
Tense: {a['tense']}
Intensity: {a['intensity']}

Chapter:
{text}
"""
    return call_llm(
        "You are a professional developmental editor.",
        prompt,
        temperature=0.3,
    )

# ============================================================
# SIDEBAR — PROJECT CONTROL
# ============================================================
with st.sidebar:
    st.header("Projects")

    names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + names)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {
                "chapters": [],
                "story_bible": "",
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
    st.title("Olivetti")
    st.write("Create or select a project to begin.")
    st.stop()

project, chapters, chapter = get_current_chapter()

# ============================================================
# TOP BAR — AUTHOR STATE (LINKED EVERYWHERE)
# ============================================================
top = st.columns([2, 2, 2, 2])
top[0].selectbox(
    "Genre",
    ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
    key="author_state.genre",
)
top[1].selectbox(
    "POV",
    ["First", "Close Third", "Omniscient"],
    key="author_state.pov",
)
top[2].selectbox(
    "Tense",
    ["Past", "Present"],
    key="author_state.tense",
)
top[3].slider(
    "Intensity",
    0.0, 1.0,
    key="author_state.intensity",
)

st.divider()

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.2, 3.2, 2])

# ---------------- LEFT — STRUCTURE ----------------
with left:
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i

    chapter["title"] = st.text_input("Chapter title", chapter["title"])

# ---------------- CENTER — WRITING ----------------
with center:
    st.subheader("Draft")
    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=560,
    )

    if st.button("Save Version"):
        save_version(chapter)

# ---------------- RIGHT — EDITORIAL TOOLS ----------------
with right:
    st.subheader("Outline")

    if st.button("Generate Outline"):
        chapter["outline"] = generate_outline(chapter["text"])

    chapter["outline"] = st.text_area(
        "",
        chapter.get("outline", ""),
        height=260,
    )

# ============================================================
# STORY BIBLE
# ============================================================
st.divider()
st.subheader("Story Bible")

project["story_bible"] = st.text_area(
    "",
    project.get("story_bible", ""),
    height=240,
)

st.caption("Olivetti — Stable Authorial Core")
