import streamlit as st
import re
from openai import OpenAI

st.set_page_config(layout="wide", page_title="Olivetti v6.0")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
if "projects" not in st.session_state:
    st.session_state.projects = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

# =========================
# HELPERS
# =========================
def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text, flags=re.IGNORECASE)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append({
            "title": parts[i].title(),
            "text": parts[i+1].strip(),
            "outline": ""
        })
    if not chapters:
        chapters.append({"title": "Chapter 1", "text": text, "outline": ""})
    return chapters

def move_chapter(project, idx, direction):
    chapters = st.session_state.projects[project]["chapters"]
    new = idx + direction
    if 0 <= new < len(chapters):
        chapters[idx], chapters[new] = chapters[new], chapters[idx]
        st.session_state.current_chapter = new

def generate_outline(text):
    prompt = f"""
Create a concise outline of this chapter.
- Bullet points
- Major beats only
- No rewriting

{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a professional story editor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return r.output_text

# =========================
# SIDEBAR — PROJECTS
# =========================
with st.sidebar:
    st.header("📁 Projects")

    names = list(st.session_state.projects.keys())
    selected = st.selectbox("Project", ["— New —"] + names)

    if selected == "— New —":
        new = st.text_input("Project name")
        if st.button("Create") and new:
            st.session_state.projects[new] = {"chapters": []}
            st.session_state.current_project = new
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = selected

    if st.session_state.current_project:
        uploaded = st.file_uploader("Import manuscript (.txt)", type=["txt"])
        if uploaded:
            text = uploaded.read().decode("utf-8")
            st.session_state.projects[
                st.session_state.current_project
            ]["chapters"] = split_into_chapters(text)
            st.session_state.current_chapter = 0

# =========================
# MAIN
# =========================
if not st.session_state.current_project:
    st.title("🫒 Olivetti")
    st.write("Create or select a project.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

# =========================
# LAYOUT
# =========================
left, center, right = st.columns([1.2, 2.5, 1.8])

# =========================
# LEFT — CHAPTERS
# =========================
with left:
    st.subheader("🧭 Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=i):
            st.session_state.current_chapter = i

    st.divider()
    chapter["title"] = st.text_input("Chapter title", chapter["title"])

    col1, col2 = st.columns(2)
    if col1.button("⬆ Up"):
        move_chapter(st.session_state.current_project, idx, -1)
    if col2.button("⬇ Down"):
        move_chapter(st.session_state.current_project, idx, 1)

# =========================
# CENTER — WRITING
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

# =========================
# RIGHT — OUTLINE
# =========================
with right:
    st.subheader("📑 Chapter Outline")

    if st.button("Generate / Update Outline"):
        with st.spinner("Analyzing chapter…"):
            chapter["outline"] = generate_outline(chapter["text"])

    chapter["outline"] = st.text_area(
        "Outline",
        chapter["outline"],
        height=420
    )

st.caption("Olivetti v6.0 — Manuscript outlining & structure")
