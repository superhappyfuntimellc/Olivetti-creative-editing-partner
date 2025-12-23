import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="🫒 Olivetti 18.1")
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
# STYLE PRESETS
# =========================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit, lightness.",
    "Lyrical": "Rhythm, imagery, musical language.",
    "Ironic": "Detached, sharp, understated humor."
}

VOICES = {
    "Neutral Editor": "Clear, professional, invisible style.",
    "Minimal": "Short sentences. Subtext. Restraint.",
    "Expressive": "Emotion-forward, dynamic voice.",
    "Hardboiled": "Dry, blunt, unsentimental.",
    "Poetic": "Figurative, flowing, evocative."
}

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

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def call_llm(system, prompt, temp=0.4):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def rewrite(text, style, bible):
    prompt = f"""
STORY BIBLE:
{bible}

STYLE:
{style}

TEXT:
{text}
"""
    return call_llm(
        "You are a precise fiction editor. Rewrite only what is provided.",
        prompt,
        0.5
    )

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
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": ""
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

# =========================
# MAIN
# =========================
if not st.session_state.current_project:
    st.title("🫒 Olivetti Studio")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

chapter = chapters[st.session_state.current_chapter]

left, center, right = st.columns([1.2, 2.6, 2.4])

# =========================
# LEFT — CHAPTERS
# =========================
with left:
    st.subheader("📚 Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i
    chapter["title"] = st.text_input("Chapter title", chapter["title"])

# =========================
# CENTER — TEXT
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    c1, c2 = st.columns(2)
    if c1.button("💾 Save Version"):
        save_version(chapter)

    chapter["workflow"] = c2.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

# =========================
# RIGHT — TOOLS
# =========================
with right:
    st.subheader("📘 Story Bible")
    project["bible"] = st.text_area(
        "Applies to all tools",
        project.get("bible", ""),
        height=160
    )

    st.divider()
    st.subheader("🎯 Target Text")
    selection = st.text_area(
        "Paste a paragraph or sentence to target (leave empty = whole chapter)",
        height=120
    )

    st.subheader("🎭 Style")
    genre = st.selectbox("Genre", GENRES.keys())
    voice = st.selectbox("Voice", VOICES.keys())
    style = f"{GENRES[genre]} {VOICES[voice]}"

    st.divider()
    if st.button("🧪 Rewrite (Preview)"):
        target = selection.strip() if selection.strip() else chapter["text"]
        chapter["preview"] = r
