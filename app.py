import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="🫒 Olivetti 20.1 — Studio",
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
        "replace_term": ""
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

# ============================================================
# HELPERS
# ============================================================
def split_chapters(text):
    parts = re.split(r"\n\s*(CHAPTER\s+\d+|Chapter\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(new_chapter(parts[i], parts[i + 1]))
    if not chapters:
        chapters.append(new_chapter("Chapter 1", text))
    return chapters

def new_chapter(title, text):
    return {
        "title": title,
        "text": text.strip(),
        "outline": "",
        "analysis": "",
        "comments": [],
        "versions": [],
        "workflow": "Draft"
    }

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def learn_voice(text):
    if len(text) > 300:
        st.session_state.voice_memory.append(text[:900])

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
Apply proportionally. Do not overwrite intent.

{samples}
"""

# ============================================================
# EDITORIAL TOOLS
# ============================================================
def generate_outline(ch):
    prompt = f"""
Create a concise chapter outline.
• Bullet points
• Structure only
• No prose rewriting

TEXT:
{ch["text"]}
"""
    ch["outline"] = llm(
        "You are a developmental editor.",
        prompt,
        0.3
    )

def rewrite_preview(ch):
    prompt = f"""
Rewrite this text.

MODE: {st.session_state.mode}
GENRE: {GENRES[st.session_state.genre]}
POV: {st.session_state.pov}
TENSE: {st.session_state.tense}
STRICTNESS: {st.session_state.strictness}

{voice_profile()}

TEXT:
{ch["text"]}
"""
    return llm(
        "You are an elite fiction editor protecting authorial voice.",
        prompt,
        0.5
    )

def analyze_strength(ch):
    prompt = f"""
Identify the strongest passages.
Explain why they work.

TEXT:
{ch["text"]}
"""
    ch["analysis"] = llm("You are a literary editor.", prompt, 0.3)

def add_comment(ch, note):
    ch["comments"].append(note)

# ============================================================
# SIDEBAR — ENGINE
# ============================================================
with st.sidebar:
    st.header("🫒 Olivetti Studio")

    st.subheader("Project")
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

    st.subheader("Style & Voice")
    st.selectbox("Genre", GENRES.keys(), key="genre")
    st.selectbox("POV", POVS, key="pov")
    st.selectbox("Tense", TENSES, key="tense")
    st.selectbox("Mode", MODES, key="mode")

    st.slider("Voice Intensity", 0.0, 1.0, key="voice_intensity")
    st.slider("Strictness", 0.0, 1.0, key="strictness")

    st.divider()
    st.subheader("Find & Replace")
    st.text_input("Find", key="find_term")
    st.text_input("Replace", key="replace_term")

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("🫒 Olivetti 20.1")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

# ============================================================
# TABS
# ============================================================
tab_write, tab_tools, tab_notes = st.tabs(
    ["✍️ Write", "🧠 Tools", "💬 Comments"]
)

# ============================================================
# WRITE TAB
# ============================================================
with tab_write:
    left, center = st.columns([1, 3])

    with left:
        st.subheader("Chapters")
        for i, ch in enumerate(chapters):
            colA, colB, colC = st.columns([6,1,1])
            colA.button(ch["title"], key=f"nav_{i}", on_click=lambda i=i: st.session_state.update({"current_chapter": i}))
            if colB.button("⬆️", key=f"up_{i}") and i > 0:
                chapters[i-1], chapters[i] = chapters[i], chapters[i-1]
            if colC.button("⬇️", key=f"down_{i}") and i < len(chapters)-1:
                chapters[i+1], chapters[i] = chapters[i], chapters[i+1]

    with center:
        chapter["title"] = st.text_input("Title", chapter["title"])
        chapter["text"] = st.text_area("", chapter["text"], height=600)

        if st.button("💾 Save Version"):
            save_version(chapter)
            learn_voice(chapter["text"])

        if st.session_state.find_term:
            chapter["text"] = chapter["text"].replace(
                st.session_state.find_term,
                st.session_state.replace_term
            )

# ============================================================
# TOOLS TAB
# ============================================================
with tab_tools:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📑 Generate Outline"):
            generate_outline(chapter)
        st.text_area("Outline", chapter.get("outline", ""), height=240)

    with col2:
        if st.button("🧠 Analyze Strength"):
            analyze_strength(chapter)
        st.text_area("Analysis", chapter.get("analysis", ""), height=240)

    if st.button("🧪 Rewrite Preview"):
        chapter["preview"] = rewrite_preview(chapter)

    if "preview" in chapter:
        st.text_area("Rewrite Preview", chapter["preview"], height=300)
        if st.button("✅ Accept Rewrite"):
            save_version(chapter)
            chapter["text"] = chapter.pop("preview")
            learn_voice(chapter["text"])

# ============================================================
# COMMENTS TAB
# ============================================================
with tab_notes:
    note = st.text_area("Add Comment")
    if st.button("Add Comment"):
        add_comment(chapter, note)

    for i, c in enumerate(chapter["comments"]):
        st.markdown(f"**Comment {i+1}:** {c}")

st.caption("🫒 Olivetti 20.1 — Studio Expansion")
