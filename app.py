import streamlit as st
import re
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti", layout="wide")

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "lock_chapter": False,
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
            "text": parts[i + 1].strip(),
            "outline": "",
            "versions": [],
            "comments": []
        })

    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "outline": "",
            "versions": [],
            "comments": []
        })

    return chapters


def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })


def get_current():
    if not st.session_state.current_project:
        st.stop()

    project = st.session_state.projects.get(st.session_state.current_project)
    if not project or not project["chapters"]:
        st.warning("Import a manuscript to begin.")
        st.stop()

    idx = max(
        0,
        min(st.session_state.current_chapter, len(project["chapters"]) - 1)
    )
    st.session_state.current_chapter = idx
    return project, project["chapters"], project["chapters"][idx]

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("Projects")

    names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + names)

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
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti")
    st.write("Create or select a project to begin.")
    st.stop()

project, chapters, chapter = get_current()

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

    st.divider()
    st.session_state.lock_chapter = st.checkbox(
        "🔒 Lock Chapter",
        value=st.session_state.lock_chapter
    )

# ---------------- CENTER — WRITING ----------------
with center:
    st.subheader("Draft")

    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=560,
        disabled=st.session_state.lock_chapter
    )

    if st.button("Save Version"):
        save_version(chapter)

# ---------------- RIGHT — EDITORIAL TOOLS ----------------
with right:
    st.subheader("Find & Replace")

    find = st.text_input("Find")
    replace = st.text_input("Replace")
    case = st.checkbox("Case sensitive")

    if find:
        flags = 0 if case else re.IGNORECASE
        matches = re.findall(find, chapter["text"], flags)
        st.caption(f"{len(matches)} matches found")

        if st.button("Replace All", disabled=st.session_state.lock_chapter):
            chapter["text"] = re.sub(find, replace, chapter["text"], flags=flags)

    st.divider()
    st.subheader("Synonyms")

    word = st.text_input("Word")
    if word:
        st.write("Suggestions:")
        st.write([f"{word}_alt1", f"{word}_alt2", f"{word}_alt3"])

    st.divider()
    st.subheader("Comments")

    comment = st.text_input("Add comment")
    if st.button("Add Comment"):
        chapter["comments"].append(comment)

    for c in chapter["comments"]:
        st.info(c)

st.caption("Olivetti 26.0 — Editorial Tools Locked")
