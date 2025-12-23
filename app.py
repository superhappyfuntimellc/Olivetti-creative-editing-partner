import streamlit as st
import re
from datetime import datetime
from collections import Counter
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti 23.8", layout="wide")
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
        "analysis": [],
        "strong_passages": [],
        "intensity": 0.5,
        "pov": "Close Third",
        "tense": "Past",
        "structure_locked": False,
        "instruction_bible": {
            "Editorial": "Revise for clarity and flow.",
            "Minimal": "Make the smallest possible improvement.",
            "Aggressive": "Rewrite boldly.",
            "Voice Locked": "Rewrite strictly matching the author’s voice."
        }
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
            "text": parts[i+1].strip(),
            "workflow": "Draft",
            "versions": []
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "workflow": "Draft",
            "versions": []
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def score_passage(p):
    words = p.split()
    sentences = re.split(r"[.!?]", p)
    verb_strength = sum(1 for w in words if w.endswith("ed") or w.endswith("ing"))
    noun_density = sum(1 for w in words if w[0].isupper())
    avg_sentence = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)

    score = (
        min(avg_sentence, 25)
        + verb_strength * 0.5
        + noun_density * 0.3
    )
    return score

def analyze_strongest(text):
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 80]
    scored = [(score_passage(p), p) for p in paragraphs]
    scored.sort(reverse=True, key=lambda x: x[0])
    return scored[:5]

# ============================================================
# TOP BAR
# ============================================================
top = st.columns([2,2,2,2])
top[0].slider("Intensity", 0.0, 1.0, key="intensity")
top[1].selectbox("POV", ["First","Close Third","Omniscient"], key="pov")
top[2].selectbox("Tense", ["Past","Present"], key="tense")
top[3].toggle("Lock Structure", key="structure_locked")

st.divider()

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("Projects")
    names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + names)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

    if not st.session_state.current_project:
        st.stop()

    project = st.session_state.projects[st.session_state.current_project]
    chapters = project["chapters"]

    st.divider()
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"ch_{i}"):
            st.session_state.current_chapter = i

# ============================================================
# MAIN
# ============================================================
chapter = chapters[st.session_state.current_chapter]

left, center, right = st.columns([1,3,2])

# ---------------- LEFT ----------------
with left:
    st.subheader("Workflow")
    st.write(chapter["workflow"])

# ---------------- CENTER ----------------
with center:
    st.subheader("Chapter Text")
    chapter["title"] = st.text_input("Title", chapter["title"])
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    if st.button("Save Version"):
        save_version(chapter)

# ---------------- RIGHT — STRONGEST PASSAGES ----------------
with right:
    st.subheader("Strongest Passages")

    if st.button("Analyze Chapter"):
        st.session_state.strong_passages = analyze_strongest(chapter["text"])

    for i, (score, passage) in enumerate(st.session_state.strong_passages):
        with st.expander(f"#{i+1} Score {round(score,2)}"):
            st.write(passage)

            if st.button("Use as Voice Anchor", key=f"anchor_{i}"):
                st.session_state.voice_bible["sample"] = passage
                st.success("Added to Voice Bible.")

st.caption("Olivetti 23.8 — Strongest Work Analyzer")
