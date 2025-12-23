import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

st.set_page_config(layout="wide", page_title="🫒 Olivetti 19.0 — Studio Mode")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
defaults = {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "selected_para": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# MODELS
# =========================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit, lightness.",
    "Lyrical": "Rhythm, imagery, musical language."
}

VOICES = {
    "Neutral": "Clear, invisible prose.",
    "Minimal": "Short, restrained sentences.",
    "Expressive": "Emotion-forward language.",
    "Hardboiled": "Dry, blunt, unsentimental.",
    "Poetic": "Figurative, musical language."
}

# =========================
# HELPERS
# =========================
def split_paragraphs(text):
    return [p for p in text.split("\n\n") if p.strip()]

def rebuild(paras):
    return "\n\n".join(paras)

def call_llm(context, intent, text):
    prompt = f"""
STORY CONTEXT:
{context}

INTENT:
{intent}

TEXT:
{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a senior fiction editor who respects constraints."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return r.output_text

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": ch["text"]
    })

# =========================
# SIDEBAR — PROJECT
# =========================
with st.sidebar:
    st.header("📁 Project")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": "",
                "characters": {}
            }
            st.session_state.current_project = name
    else:
        st.session_state.current_project = choice

    project = st.session_state.projects.get(st.session_state.current_project)

    if project:
        st.divider()
        st.subheader("📘 Story Bible")
        project["bible"] = st.text_area("", project["bible"], height=120)

        st.divider()
        st.subheader("🧍 Characters")
        cname = st.text_input("New character")
        if st.button("Add Character") and cname:
            project["characters"][cname] = {
                "voice": "",
                "motivation": "",
                "constraints": ""
            }

        for c, data in project["characters"].items():
            with st.expander(c):
                data["voice"] = st.text_area("Voice", data["voice"])
                data["motivation"] = st.text_area("Motivation", data["motivation"])
                data["constraints"] = st.text_area("Constraints", data["constraints"])

# =========================
# MAIN
# =========================
if not project:
    st.title("🫒 Olivetti Studio")
    st.stop()

# Ensure one chapter
if not project["chapters"]:
    project["chapters"].append({
        "title": "Chapter 1",
        "text": "",
        "scene": {"pov": "", "location": "", "intent": ""},
        "versions": [],
        "history": [],
        "outputs": []
    })

chapter = project["chapters"][st.session_state.current_chapter]
paragraphs = split_paragraphs(chapter["text"])

left, center, right = st.columns([1.1, 2.3, 2.6])

# =========================
# LEFT — PARAGRAPHS
# =========================
with left:
    st.subheader("¶ Paragraphs")
    for i, p in enumerate(paragraphs):
        if st.button(f"¶ {i+1}", key=f"p{i}"):
            st.session_state.selected_para = i

# =========================
# CENTER — TEXT
# =========================
with center:
    st.subheader("✍️ Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    if st.button("💾 Save Version"):
        save_version(chapter)

# =========================
# RIGHT — STUDIO
# =========================
with right:
    st.subheader("🎬 Scene Context")
    chapter["scene"]["pov"] = st.selectbox(
        "POV Character",
        [""] + list(project["characters"].keys())
    )
    chapter["scene"]["location"] = st.text_input("Location", chapter["scene"]["location"])
    chapter["scene"]["intent"] = st.text_input("Scene Intent", chapter["scene"]["intent"])

    st.divider()
    st.subheader("🧠 Command Palette")

    intent = st.text_in_
