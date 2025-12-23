import streamlit as st
import re
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 22.3")
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
# DATA
# ============================================================
def make_voice_bible():
    return {
        "sentence_architecture": "",
        "rhythm": "",
        "diction": "",
        "distance": "",
        "intensity": "",
        "forbidden": ""
    }

def make_project():
    return {
        "chapters": [],
        "voice_bible": make_voice_bible()
    }

def make_chapter(title, text):
    return {"title": title, "text": text, "outline": ""}

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(make_chapter(parts[i].title(), parts[i + 1].strip()))
    if not chapters:
        chapters.append(make_chapter("Chapter 1", text))
    return chapters

# ============================================================
# VOICE BIBLE TRAINER
# ============================================================
def train_voice_bible(sample):
    prompt = f"""
Analyze this passage and extract a VOICE BIBLE.

Return labeled sections ONLY:

SENTENCE ARCHITECTURE
RHYTHM & CADENCE
DICTION RULES
NARRATIVE DISTANCE
INTENSITY ENVELOPE
FORBIDDEN MOVES

Do not rewrite. Do not summarize the passage.

TEXT:
{sample}
"""
    raw = llm("You are a master literary stylist.", prompt, 0.3)

    bible = make_voice_bible()
    current = None
    for line in raw.splitlines():
        l = line.lower()
        if "sentence architecture" in l:
            current = "sentence_architecture"
        elif "rhythm" in l:
            current = "rhythm"
        elif "diction" in l:
            current = "diction"
        elif "distance" in l:
            current = "distance"
        elif "intensity" in l:
            current = "intensity"
        elif "forbidden" in l:
            current = "forbidden"
        elif current:
            bible[current] += line + "\n"

    return bible

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
    st.title("🫒 Olivetti 22.3")
    st.write("Create or select a project.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]
voice_bible = project["voice_bible"]

left, center, right = st.columns([1.2, 3.2, 2.6])

# ============================================================
# LEFT
# ============================================================
with left:
    st.subheader("Chapters")
    for i, c in enumerate(chapters):
        if st.button(f"{i+1}. {c['title']}"):
            st.session_state.current_chapter = i

# ============================================================
# CENTER
# ============================================================
chapter = chapters[st.session_state.current_chapter]
with center:
    st.subheader(chapter["title"])
    chapter["text"] = st.text_area("Text", chapter["text"], height=540)

# ============================================================
# RIGHT — VOICE BIBLE
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")

    sample = st.text_area(
        "Train from your strongest passage",
        height=140
    )

    if st.button("Build / Update Voice Bible") and sample:
        with st.spinner("Extracting voice canon…"):
            project["voice_bible"] = train_voice_bible(sample)
        st.success("Voice Bible updated.")

    tabs = {
        "Sentence": "sentence_architecture",
        "Rhythm": "rhythm",
        "Diction": "diction",
        "Distance": "distance",
        "Intensity": "intensity",
        "Forbidden": "forbidden"
    }

    section = st.selectbox("Section", list(tabs.keys()))
    key = tabs[section]

    voice_bible[key] = st.text_area(
        section,
        voice_bible[key],
        height=260
    )

st.caption("Olivetti 22.3 — Voice Is Canon")
