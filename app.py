import streamlit as st
import re
from datetime import datetime
from collections import Counter
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti 23.4",
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
        "voice_bible": {},
        "instruction_bible": {},
        "analysis": [],
        "intensity": 0.5,
        "pov": "Close Third",
        "tense": "Past"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# PRESETS
# ============================================================
GENRES = {
    "Literary": "Elegant, interior, controlled.",
    "Noir": "Hard, clipped, concrete.",
    "Thriller": "Fast, tense, escalating.",
    "Lyrical": "Musical, image-rich.",
    "Ironic": "Detached, precise."
}

POVS = ["First", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]

# ============================================================
# HELPERS
# ============================================================
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

def call_llm(system, prompt, temperature=0.4):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return response.output_text

# ============================================================
# VOICE TRAINER
# ============================================================
def train_voice(sample):
    words = sample.split()
    sentences = re.split(r"[.!?]", sample)

    return {
        "avg_sentence_length": sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1),
        "vocab_richness": len(set(words)) / max(len(words), 1),
        "top_words": Counter(words).most_common(15),
        "sample": sample[:1000]
    }

# ============================================================
# ANALYZER
# ============================================================
def analyze_text(text, voice_profile):
    notes = []

    avg_len = sum(len(s.split()) for s in re.split(r"[.!?]", text) if s.strip()) / max(len(text.split(".")), 1)
    if avg_len > voice_profile.get("avg_sentence_length", avg_len) * 1.3:
        notes.append("Sentence length drifting longer than voice baseline.")

    weak_verbs = ["was", "were", "is", "are"]
    weak_count = sum(text.lower().count(w) for w in weak_verbs)
    if weak_count > 10:
        notes.append("High passive / weak verb density.")

    return notes

# ============================================================
# TOP BAR
# ============================================================
with st.container():
    cols = st.columns([2,2,2,2,2,2])
    if cols[0].button("Import TXT"):
        upload = st.file_uploader("Upload .txt", type=["txt"], label_visibility="collapsed")
        if upload and st.session_state.current_project:
            text = upload.read().decode("utf-8")
            st.session_state.projects[st.session_state.current_project]["chapters"] = split_into_chapters(text)

    if cols[1].button("Export Manuscript"):
        if st.session_state.current_project:
            manuscript = "\n\n".join(c["text"] for c in st.session_state.projects[st.session_state.current_project]["chapters"])
            st.download_button("Download", manuscript, file_name="manuscript.txt")

    cols[2].slider("Intensity", 0.0, 1.0, key="intensity")
    cols[3].selectbox("POV", POVS, key="pov")
    cols[4].selectbox("Tense", TENSES, key="tense")
    cols[5].button("Snapshot")

st.divider()

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("Projects")
    project_names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + project_names)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 23.4")
    st.write("Create or select a project.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

left, center = st.columns([1, 3])

# ============================================================
# LEFT — STRUCTURE
# ============================================================
with left:
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"ch_{i}"):
            st.session_state.current_chapter = i

    chapter["title"] = st.text_input("Chapter Title", chapter["title"])

# ============================================================
# CENTER — EDITOR + TOOLS
# ============================================================
with center:
    st.subheader("Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=500)

    c1, c2, c3 = st.columns(3)
    if c1.button("Save Version"):
        save_version(chapter)

    chapter["workflow"] = c2.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

    if c3.button("Analyze"):
        if st.session_state.voice_bible:
            st.session_state.analysis = analyze_text(
                chapter["text"],
                st.session_state.voice_bible
            )

    st.divider()

    if st.session_state.analysis:
        st.subheader("Analyzer Notes")
        for note in st.session_state.analysis:
            st.warning(note)

    st.divider()

    st.subheader("Voice Trainer")
    sample = st.text_area("Anchor Sample (your best prose)", height=120)
    if st.button("Train Voice"):
        st.session_state.voice_bible = train_voice(sample)
        st.success("Voice profile updated.")

    if st.session_state.voice_bible:
        st.json(st.session_state.voice_bible)

st.caption("Olivetti 23.4 — Professional Writing Engine")
