import streamlit as st
import re
from datetime import datetime
from collections import Counter
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti 23.5",
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
        "analysis": [],
        "intensity": 0.5,
        "pov": "Close Third",
        "tense": "Past",
        "instruction_bible": {
            "Editorial": "Revise for clarity, consistency, and narrative flow without changing voice.",
            "Minimal": "Make the smallest possible improvement. Preserve original wording.",
            "Aggressive": "Rewrite boldly for impact, tension, and sharpness.",
            "Voice Locked": "Rewrite strictly matching the author’s voice profile. Do not drift.",
        }
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
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature
    )
    return r.output_text

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
# AI ACTION ENGINE (FULLY WIRED)
# ============================================================
def ai_action(action_name, text, instruction_key):
    instruction = st.session_state.instruction_bible[instruction_key]

    voice_rules = ""
    if st.session_state.voice_bible:
        voice_rules = f"""
VOICE PROFILE:
Average sentence length: {st.session_state.voice_bible['avg_sentence_length']}
Vocabulary richness: {st.session_state.voice_bible['vocab_richness']}
"""

    prompt = f"""
ACTION: {action_name}

INSTRUCTIONS:
{instruction}

POV: {st.session_state.pov}
TENSE: {st.session_state.tense}
INTENSITY: {st.session_state.intensity}

{voice_rules}

TEXT:
{text}
"""

    return call_llm(
        "You are a professional fiction editor executing a specific revision task.",
        prompt,
        temperature=st.session_state.intensity
    )

# ============================================================
# TOP BAR
# ============================================================
with st.container():
    c = st.columns([2,2,2,2,2,2])
    c[0].slider("Intensity", 0.0, 1.0, key="intensity")
    c[1].selectbox("POV", POVS, key="pov")
    c[2].selectbox("Tense", TENSES, key="tense")
    c[3].button("Snapshot")
    c[4].button("Export Manuscript")
    c[5].button("Settings")

st.divider()

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("Projects")
    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

    st.divider()
    st.subheader("Instruction Bible")

    for k in list(st.session_state.instruction_bible.keys()):
        st.session_state.instruction_bible[k] = st.text_area(
            k,
            st.session_state.instruction_bible[k],
            height=80
        )

    new_key = st.text_input("New Instruction Set")
    if st.button("Add Instruction") and new_key:
        st.session_state.instruction_bible[new_key] = ""

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 23.5")
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
# LEFT — CHAPTER NAV
# ============================================================
with left:
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"ch_{i}"):
            st.session_state.current_chapter = i

# ============================================================
# CENTER — EDITOR + AI TOOLS
# ============================================================
with center:
    st.subheader("Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=420)

    save_version_btn, workflow = st.columns(2)
    if save_version_btn.button("Save Version"):
        save_version(chapter)

    chapter["workflow"] = workflow.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

    st.divider()
    st.subheader("AI Actions")

    instruction_choice = st.selectbox(
        "Instruction Set",
        list(st.session_state.instruction_bible.keys())
    )

    a, b, c, d = st.columns(4)

    if a.button("Rewrite"):
        chapter["preview"] = ai_action("Rewrite", chapter["text"], instruction_choice)

    if b.button("Tighten"):
        chapter["preview"] = ai_action("Tighten", chapter["text"], instruction_choice)

    if c.button("Expand"):
        chapter["preview"] = ai_action("Expand", chapter["text"], instruction_choice)

    if d.button("Clarify"):
        chapter["preview"] = ai_action("Clarify", chapter["text"], instruction_choice)

    if "preview" in chapter:
        st.divider()
        st.subheader("Preview")
        st.text_area("AI Preview", chapter["preview"], height=240)

        accept, reject = st.columns(2)
        if accept.button("Accept"):
            save_version(chapter)
            chapter["text"] = chapter.pop("preview")

        if reject.button("Reject"):
            chapter.pop("preview")

    st.divider()
    st.subheader("Voice Trainer")
    sample = st.text_area("Anchor Sample", height=120)
    if st.button("Train Voice"):
        st.session_state.voice_bible = train_voice(sample)
        st.success("Voice trained.")

    if st.session_state.voice_bible:
        st.json(st.session_state.voice_bible)

st.caption("Olivetti 23.5 — Instruction-Aware Writing Engine")
