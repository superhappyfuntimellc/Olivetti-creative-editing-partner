import streamlit as st
import re
from openai import OpenAI

st.set_page_config(layout="wide", page_title="Olivetti v5.0")
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

if "style_sample" not in st.session_state:
    st.session_state.style_sample = ""

# =========================
# HELPERS
# =========================
def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text, flags=re.IGNORECASE)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append({
            "title": parts[i].title(),
            "text": parts[i+1].strip()
        })
    if not chapters:
        chapters.append({"title": "Chapter 1", "text": text})
    return chapters

def move_chapter(project, idx, direction):
    chapters = st.session_state.projects[project]["chapters"]
    new = idx + direction
    if 0 <= new < len(chapters):
        chapters[idx], chapters[new] = chapters[new], chapters[idx]
        st.session_state.current_chapter = new

def ai_rewrite(text, style, tense, sample):
    system = "You are a professional novelist and editor."

    if sample:
        system += "\nMatch the user's writing style sample."

    prompt = f"""
Rewrite the following chapter.
Style: {style}
Tense: {tense}

{text}
"""

    if sample:
        prompt = f"STYLE SAMPLE:\n{sample}\n\n{prompt}"

    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
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

left, right = st.columns([2, 3])

# =========================
# LEFT — STRUCTURE
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
# RIGHT — WRITING + AI
# =========================
with right:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=420)

    st.divider()
    st.subheader("🤖 AI Tools")

    style = st.selectbox(
        "Genre / Voice",
        ["Literary", "Noir", "Lyrical", "Ironic", "Thriller"]
    )

    tense = st.radio("Tense", ["Past", "Present"], horizontal=True)

    st.session_state.style_sample = st.text_area(
        "Match My Writing Style (optional)",
        st.session_state.style_sample,
        height=120
    )

    if st.button("✨ Rewrite Chapter"):
        with st.spinner("Rewriting…"):
            chapter["text"] = ai_rewrite(
                chapter["text"],
                style,
                tense,
                st.session_state.style_sample
            )

st.caption("Olivetti v5.0 — AI writing tools integrated")
