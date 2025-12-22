import streamlit as st
import re

st.set_page_config(layout="wide", page_title="Olivetti v4.1")

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
        title = parts[i].strip().title()
        body = parts[i + 1].strip()
        chapters.append({"title": title, "text": body})
    if not chapters:
        chapters.append({"title": "Chapter 1", "text": text})
    return chapters

def move_chapter(project, idx, direction):
    chapters = st.session_state.projects[project]["chapters"]
    new_idx = idx + direction
    if 0 <= new_idx < len(chapters):
        chapters[idx], chapters[new_idx] = chapters[new_idx], chapters[idx]
        st.session_state.current_chapter = new_idx

# =========================
# SIDEBAR — PROJECTS
# =========================
with st.sidebar:
    st.header("📁 Projects")

    project_names = list(st.session_state.projects.keys())

    selected = st.selectbox(
        "Select project",
        ["— Create New —"] + project_names
    )

    if selected == "— Create New —":
        new_name = st.text_input("New project name")
        if st.button("Create project") and new_name:
            st.session_state.projects[new_name] = {
                "chapters": []
            }
            st.session_state.current_project = new_name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = selected

    if st.session_state.current_project:
        st.divider()
        new_title = st.text_input(
            "Rename project",
            st.session_state.current_project
        )
        if new_title and new_title != st.session_state.current_project:
            st.session_state.projects[new_title] = st.session_state.projects.pop(
                st.session_state.current_project
            )
            st.session_state.current_project = new_title

        uploaded = st.file_uploader(
            "Import manuscript (.txt)",
            type=["txt"],
            key="uploader"
        )
        if uploaded:
            text = uploaded.read().decode("utf-8")
            st.session_state.projects[st.session_state.current_project]["chapters"] = (
                split_into_chapters(text)
            )
            st.session_state.current_chapter = 0

        st.divider()
        st.subheader("Chapters")
        chapters = st.session_state.projects[st.session_state.current_project]["chapters"]
        for i, ch in enumerate(chapters):
            if st.button(f"{i+1}. {ch['title']}", key=f"{i}_{ch['title']}"):
                st.session_state.current_chapter = i

# =========================
# MAIN VIEW
# =========================
if not st.session_state.current_project:
    st.title("🫒 Olivetti")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.title(st.session_state.current_project)
    st.write("Import a manuscript to populate this project.")
    st.stop()

left, right = st.columns([2, 3])
idx = st.session_state.current_chapter
chapter = chapters[idx]

# =========================
# LEFT — STRUCTURE
# =========================
with left:
    st.subheader("🧭 Outline")

    chapter["title"] = st.text_input("Chapter title", chapter["title"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬆ Move Up"):
            move_chapter(st.session_state.current_project, idx, -1)
    with col2:
        if st.button("⬇ Move Down"):
            move_chapter(st.session_state.current_project, idx, 1)

    st.divider()

    find = st.text_input("Find")
    replace = st.text_input("Replace")
    if st.button("Replace in chapter") and find:
        chapter["text"] = chapter["text"].replace(find, replace)

# =========================
# RIGHT — WRITING
# =========================
with right:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=520
    )

    st.caption("Autosaved in project session")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Olivetti v4.1 — Project-based manuscript workspace")
