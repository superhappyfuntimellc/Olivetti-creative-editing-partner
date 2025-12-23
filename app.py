import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="🫒 Olivetti 18.2")
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
# TOOLS
# =========================
TOOLS = {
    "Rewrite": "Rewrite the text while preserving meaning.",
    "Expand": "Expand the text with richer detail and depth.",
    "Compress": "Condense the text without losing meaning.",
    "Clarify": "Make the text clearer and more precise.",
    "Heighten Tension": "Increase tension, stakes, and urgency.",
    "Continue": "Continue the text naturally."
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
            "workflow": "Draft",
            "versions": [],
            "outputs": []
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "workflow": "Draft",
            "versions": [],
            "outputs": []
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def call_llm(intent, text, style, bible, temp=0.5):
    prompt = f"""
STORY BIBLE:
{bible}

STYLE:
{style}

INTENT:
{intent}

TEXT:
{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a professional fiction editor."},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

# =========================
# SIDEBAR
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

left, center, right = st.columns([1.1, 2.6, 2.5])

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
    project["bible"] = st.text_area("Global canon", project.get("bible", ""), height=140)

    st.divider()
    st.subheader("🎯 Target")
    selection = st.text_area(
        "Paste a paragraph/sentence (empty = whole chapter)",
        height=110
    )
    target = selection.strip() if selection.strip() else chapter["text"]

    st.subheader("🎭 Style")
    genre = st.selectbox("Genre", GENRES.keys())
    voice = st.selectbox("Voice", VOICES.keys())
    style = f"{GENRES[genre]} {VOICES[voice]}"

    st.divider()
    st.subheader("🧰 Tools")

    cols = st.columns(2)
    for i, tool in enumerate(TOOLS):
        if cols[i % 2].button(tool):
            output = call_llm(
                TOOLS[tool],
                target,
                style,
                project.get("bible", "")
            )
            chapter["outputs"].append({
                "tool": tool,
                "target": target,
                "text": output
            })

    if chapter["outputs"]:
        st.divider()
        st.subheader("🧪 Outputs")
        for idx, out in enumerate(chapter["outputs"]):
            st.markdown(f"**{out['tool']}**")
            st.text_area("", out["text"], height=140, key=f"out_{idx}")
            if st.button(f"✅ Accept {out['tool']}", key=f"acc_{idx}"):
                save_version(chapter)
                if selection.strip():
