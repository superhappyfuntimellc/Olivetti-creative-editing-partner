import streamlit as st
import re
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 22.1")
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
# LLM HELPER
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
def make_story_bible():
    return {
        "voice_profile": "",
        "strength_report": "",
        "pov": "Close Third",
        "tense": "Past"
    }

def make_chapter(title, text):
    return {
        "title": title,
        "text": text,
        "outline": ""
    }

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(make_chapter(parts[i].title(), parts[i + 1].strip()))
    if not chapters:
        chapters.append(make_chapter("Chapter 1", text))
    return chapters

# ============================================================
# VOICE TRAINER
# ============================================================
def train_voice(sample):
    prompt = f"""
Analyze this passage for AUTHORIAL VOICE.

Return bullet points only:
- Sentence length habits
- Syntax patterns
- Diction level
- Rhythm and cadence
- Emotional distance

TEXT:
{sample}
"""
    return llm("You are a literary voice analyst.", prompt, 0.3)

# ============================================================
# TEXT ANALYZER
# ============================================================
def analyze_strength(chapters, voice_profile):
    prompt = f"""
Score each chapter from 1–10 on:
- Voice consistency
- Density
- Specificity
- Momentum

Identify strongest and weakest chapters briefly.

VOICE PROFILE:
{voice_profile}

CHAPTERS:
{[(c['title'], c['text'][:1200]) for c in chapters]}
"""
    return llm("You are a senior fiction editor.", prompt, 0.3)

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
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": make_story_bible()
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

# ============================================================
# MAIN GUARD
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 22.1")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]
bible = project["bible"]

# ============================================================
# LAYOUT (LOCKED — DO NOT MOVE)
# ============================================================
left, center, right = st.columns([1.1, 3.6, 2.3])

# ============================================================
# LEFT — CHAPTER LIST
# ============================================================
with left:
    st.subheader("Chapters")
    for i, c in enumerate(chapters):
        if st.button(f"{i+1}. {c['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i

# ============================================================
# CENTER — MANUSCRIPT
# ============================================================
chapter = chapters[st.session_state.current_chapter]

with center:
    st.subheader(chapter["title"])
    chapter["text"] = st.text_area(
        "Chapter Text",
        chapter["text"],
        height=560
    )

# ============================================================
# RIGHT — VOICE + ANALYSIS
# ============================================================
with right:
    st.subheader("Voice Trainer")

    voice_sample = st.text_area(
        "Paste your strongest passage",
        height=140
    )

    if st.button("Train Voice") and voice_sample:
        with st.spinner("Training voice model..."):
            bible["voice_profile"] = train_voice(voice_sample)

    if bible["voice_profile"]:
        st.text_area(
            "Learned Voice Profile",
            bible["voice_profile"],
            height=200
        )

    st.divider()
    st.subheader("Text Strength Analyzer")

    if st.button("Analyze Manuscript"):
        with st.spinner("Analyzing chapters..."):
            bible["strength_report"] = analyze_strength(
                chapters,
                bible["voice_profile"]
            )

    if bible["strength_report"]:
        st.text_area(
            "Strength Report",
            bible["strength_report"],
            height=260
        )

st.caption("Olivetti 22.1 — Stable, Author-Centric, Learning Engine")
