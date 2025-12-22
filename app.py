import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

st.set_page_config(layout="wide", page_title="Olivetti v7.8")
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

def move_chapter(project, idx, direction):
    chapters = st.session_state.projects[project]["chapters"]
    new = idx + direction
    if 0 <= new < len(chapters):
        chapters[idx], chapters[new] = chapters[new], chapters[idx]
        st.session_state.current_chapter = new

def save_version(chapter):
    chapter["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": chapter["text"]
    })

def restore_version(chapter, index):
    chapter["text"] = chapter["versions"][index]["text"]

def generate_outline(text):
    prompt = f"""
Create a concise chapter outline.
• Bullet points
• Major beats only
• No rewriting

{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a professional developmental editor."},
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

# =========================
# MAIN
# =========================
if not st.session_state.current_project:
    st.title("🫒 Olivetti")
    st.write("Create or select a project to begin.")
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
left, center, right = st.columns([1.2, 2.8, 2.0])

# =========================
# LEFT — CHAPTER LIST
# =========================
with left:
    st.subheader("📚 Chapters")

    for i, ch in enumerate(chapters):
        label = f"{i+1}. {ch['title']} ({ch['workflow']})"
        if st.button(label, key=f"chap_{i}"):
            st.session_state.current_chapter = i

    st.divider()
    chapter["title"] = st.text_input("Chapter title", chapter["title"])

    col1, col2 = st.columns(2)
    if col1.button("⬆ Move Up"):
        move_chapter(st.session_state.current_project, idx, -1)
    if col2.button("⬇ Move Down"):
        move_chapter(st.session_state.current_project, idx, 1)

# =========================
# CENTER — WRITING
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    colA, colB = st.columns(2)
    if colA.button("💾 Save Version"):
        save_version(chapter)
    chapter["workflow"] = colB.selectbox(
        "Workflow Stage",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

# =========================
# RIGHT — OUTLINE + HISTORY
# =========================
with right:
    st.subheader("📑 Outline")

    if st.button("Generate / Update Outline"):
        with st.spinner("Analyzing chapter…"):
            chapter["outline"] = generate_outline(chapter["text"])

    chapter["outline"] = st.text_area("Outline", chapter["outline"], height=220)

    st.divider()
    st.subheader("🧾 Version History")

    if chapter["versions"]:
        for i, v in enumerate(reversed(chapter["versions"])):
            idx_restore = len(chapter["versions"]) - 1 - i
            if st.button(f"Restore {v['time']}", key=f"restore_{i}"):
                restore_version(chapter, idx_restore)
    else:
        st.caption("No saved versions yet.")

st.caption("Olivetti v7.8 — Built for long-form writers")
