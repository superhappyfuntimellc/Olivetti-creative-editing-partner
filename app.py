import streamlit as st
import re
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 23.1")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

# ============================================================
# LLM
# ============================================================
def llm(system, prompt, temp=0.3):
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
# DATA STRUCTURES
# ============================================================
def make_instruction_bible():
    return {
        "Default Literary": "Write with restraint, precision, and interiority.",
        "Hard Edit": "Be blunt. Cut excess. Preserve voice. No mercy.",
        "Developmental": "Focus on structure, clarity, and intent.",
        "Experimental": "Take risks. Push language. Surprise the reader."
    }

def make_project():
    return {
        "chapters": [],
        "instruction_bible": make_instruction_bible()
    }

def make_chapter(title, text):
    return {"title": title, "text": text}

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(make_chapter(parts[i].title(), parts[i + 1].strip()))
    if not chapters:
        chapters.append(make_chapter("Chapter 1", text))
    return chapters

# ============================================================
# INTENSITY MAPPER
# ============================================================
def intensity_guidance(level):
    return {
        1: "Very restrained. Minimal changes. Preserve original phrasing.",
        2: "Light touch. Subtle improvements only.",
        3: "Moderate revision. Clarify without risk.",
        4: "Assertive. Improve flow and precision.",
        5: "Bold. Sharpen language and rhythm.",
        6: "Aggressive. Cut hard. Elevate voice.",
        7: "Very aggressive. Transform weak lines.",
        8: "High risk. Push style and compression.",
        9: "Extreme. Radical but coherent changes.",
        10: "Maximum intensity. Only for experiments."
    }[level]

# ============================================================
# AI ACTIONS
# ============================================================
def rewrite_with_controls(text, instructions, intensity):
    prompt = f"""
INSTRUCTIONS (MANDATORY):
{instructions}

INTENSITY LEVEL: {intensity}/10
{intensity_guidance(intensity)}

Rewrite the text accordingly.
Preserve meaning unless intensity implies risk.

TEXT:
{text}
"""
    return llm("You are a professional fiction editor.", prompt, 0.5)

def comment_with_controls(text, instructions, intensity):
    prompt = f"""
INSTRUCTIONS (MANDATORY):
{instructions}

INTENSITY LEVEL: {intensity}/10
{intensity_guidance(intensity)}

Give margin comments only.
No rewriting.

TEXT:
{text}
"""
    return llm("You are a senior editor.", prompt, 0.3)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Projects")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = make_project()
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

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("🫒 Olivetti 23.1")
    st.write("Create or select a project.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]
instruction_bible = project["instruction_bible"]

left, center, right = st.columns([1.2, 3.2, 2.6])

# ============================================================
# LEFT — CHAPTERS
# ============================================================
with left:
    st.subheader("Chapters")
    for i, c in enumerate(chapters):
        if st.button(f"{i+1}. {c['title']}"):
            st.session_state.current_chapter = i

# ============================================================
# CENTER — TEXT
# ============================================================
chapter = chapters[st.session_state.current_chapter]
with center:
    st.subheader(chapter["title"])
    chapter["text"] = st.text_area("Text", chapter["text"], height=540)

# ============================================================
# RIGHT — CONTROLS
# ============================================================
with right:
    st.subheader("📜 Instruction & Intensity")

    names = list(instruction_bible.keys())
    selected = st.selectbox("Instruction Set", names)

    instruction_bible[selected] = st.text_area(
        "Instructions",
        instruction_bible[selected],
        height=180
    )

    intensity = st.slider(
        "Intensity",
        1, 10, 5,
        help="Controls how hard the AI pushes"
    )

    st.divider()
    st.subheader("AI Actions")

    if st.button("Rewrite (Preview)"):
        with st.spinner("Rewriting…"):
            chapter["preview"] = rewrite_with_controls(
                chapter["text"],
                instruction_bible[selected],
                intensity
            )

    if st.button("Comment (Margin Notes)"):
        with st.spinner("Commenting…"):
            chapter["comments"] = comment_with_controls(
                chapter["text"],
                instruction_bible[selected],
                intensity
            )

    if chapter.get("preview"):
        st.text_area("Rewrite Preview", chapter["preview"], height=200)
        if st.button("Accept Rewrite"):
            chapter["text"] = chapter.pop("preview")

    if chapter.get("comments"):
        st.text_area("Comments", chapter["comments"], height=200)

st.caption("Olivetti 23.1 — Instructions × Intensity")
