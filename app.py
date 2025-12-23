import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti 20.2 — Editorial Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "voice_memory": [],
        "voice_intensity": 0.6,
        "strictness": 0.5,
        "genre": "Literary",
        "pov": "Close Third",
        "tense": "Past",
        "mode": "Prose",
        "find_term": "",
        "replace_term": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# PRESETS
# ============================================================
GENRES = {
    "Literary": "Elegant prose, depth, interiority.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Noir": "Hard-edged, cynical, concrete.",
    "Comedy": "Timing, wit, irony.",
    "Lyrical": "Musical language, imagery."
}

POVS = ["First", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]
MODES = ["Prose", "Screenplay"]
WORKFLOWS = ["Draft", "Revise", "Polish", "Final"]

# ============================================================
# HELPERS
# ============================================================
def new_chapter(title, text):
    return {
        "title": title,
        "text": text.strip(),
        "outline": "",
        "analysis": "",
        "comments": [],
        "versions": [],
        "workflow": "Draft",
        "strengths": [],
        "warnings": []
    }

def split_chapters(text):
    parts = re.split(r"\n\s*(CHAPTER\s+\d+|Chapter\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(new_chapter(parts[i], parts[i + 1]))
    if not chapters:
        chapters.append(new_chapter("Chapter 1", text))
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def learn_voice(text):
    if len(text) > 300:
        st.session_state.voice_memory.append(text[:800])

def llm(system, prompt, temp=0.4):
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
# VOICE PROFILE
# ============================================================
def voice_profile():
    if not st.session_state.voice_memory:
        return ""
    samples = "\n\n".join(st.session_state.voice_memory[-5:])
    return f"""
AUTHOR VOICE PROFILE
Intensity: {st.session_state.voice_intensity:.2f}

{samples}
"""

# ============================================================
# ADAPTIVE STRICTNESS
# ============================================================
def adaptive_strictness(workflow):
    base = st.session_state.strictness
    if workflow == "Draft":
        return max(0.1, base - 0.2)
    if workflow == "Revise":
        return base
    if workflow == "Polish":
        return min(0.9, base + 0.2)
    if workflow == "Final":
        return 1.0
    return base

# ============================================================
# EDITORIAL INTELLIGENCE
# ============================================================
def analyze_strengths(ch):
    prompt = f"""
Identify the strongest paragraphs in this chapter.
Return:
• Quoted paragraph
• One-sentence reason why it works

TEXT:
{ch["text"]}
"""
    ch["strengths"] = llm(
        "You are a senior literary editor.",
        prompt,
        0.3
    )

def detect_voice_deviation(ch):
    prompt = f"""
Compare this text to the author's established voice.
If deviations exist, list them briefly.
If not, say 'No significant deviation.'

VOICE:
{voice_profile()}

TEXT:
{ch["text"]}
"""
    ch["warnings"] = llm(
        "You are an editorial continuity specialist.",
        prompt,
        0.3
    )

def rewrite_preview(ch):
    strict = adaptive_strictness(ch["workflow"])
    prompt = f"""
Rewrite this text.

MODE: {st.session_state.mode}
GENRE: {GENRES[st.session_state.genre]}
POV: {st.session_state.pov}
TENSE: {st.session_state.tense}
STRICTNESS: {strict}

{voice_profile()}

TEXT:
{ch["text"]}
"""
    return llm(
        "You are an elite fiction editor protecting authorial voice.",
        prompt,
        0.5
    )

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Olivetti Studio")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
    else:
        st.session_state.current_project = choice

    if st.session_state.current_project:
        upload = st.file_uploader("Import manuscript (.txt)")
        if upload:
            txt = upload.read().decode("utf-8")
            st.session_state.projects[
                st.session_state.current_project
            ]["chapters"] = split_chapters(txt)

    st.divider()

    st.subheader("Style")
    st.selectbox("Genre", GENRES.keys(), key="genre")
    st.selectbox("POV", POVS, key="pov")
    st.selectbox("Tense", TENSES, key="tense")
    st.selectbox("Mode", MODES, key="mode")

    st.slider("Voice Intensity", 0.0, 1.0, key="voice_intensity")
    st.slider("Strictness", 0.0, 1.0, key="strictness")

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 20.2")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

tab_write, tab_intel, tab_comments = st.tabs(
    ["Write", "Editorial Intel", "Comments"]
)

# ============================================================
# WRITE TAB
# ============================================================
with tab_write:
    left, center = st.columns([1, 3])

    with left:
        for i, ch in enumerate(chapters):
            if st.button(ch["title"], key=f"nav_{i}"):
                st.session_state.current_chapter = i

    with center:
        chapter["title"] = st.text_input("Title", chapter["title"])
        chapter["workflow"] = st.selectbox(
            "Workflow",
            WORKFLOWS,
            index=WORKFLOWS.index(chapter["workflow"])
        )
        chapter["text"] = st.text_area("", chapter["text"], height=600)

        if st.button("Save Version"):
            save_version(chapter)
            learn_voice(chapter["text"])

# ============================================================
# EDITORIAL INTEL TAB
# ============================================================
with tab_intel:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Analyze Strongest Passages"):
            analyze_strengths(chapter)
        st.text_area(
            "Strong Passages",
            chapter.get("strengths", ""),
            height=260
        )

        if st.button("Promote Strengths to Voice Memory"):
            learn_voice(chapter.get("strengths", ""))

    with col2:
        if st.button("Check Voice Deviation"):
            detect_voice_deviation(chapter)
        st.text_area(
            "Voice Deviation Warnings",
            chapter.get("warnings", ""),
            height=260
        )

    if st.button("Rewrite Preview"):
        chapter["preview"] = rewrite_preview(chapter)

    if "preview" in chapter:
        st.text_area("Rewrite Preview", chapter["preview"], height=300)
        if st.button("Accept Rewrite"):
            save_version(chapter)
            chapter["text"] = chapter.pop("preview")
            learn_voice(chapter["text"])

# ============================================================
# COMMENTS TAB
# ============================================================
with tab_comments:
    note = st.text_area("Add Comment")
    if st.button("Add Comment"):
        chapter["comments"].append(note)

    for i, c in enumerate(chapter["comments"]):
        st.markdown(f"{i+1}. {c}")

st.caption("Olivetti 20.2 — Editorial Intelligence Layer")
