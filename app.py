import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Olivetti 20.1")
client = OpenAI()

# =========================
# SESSION STATE SAFETY
# =========================
st.session_state.setdefault("projects", {})
st.session_state.setdefault("current_project", None)
st.session_state.setdefault("current_chapter", 0)

# =========================
# STYLE REGISTRIES
# =========================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit.",
    "Lyrical": "Rhythmic, image-forward language."
}

VOICES = {
    "Neutral Editor": "Invisible, professional tone.",
    "Minimal": "Spare, restrained sentences.",
    "Expressive": "Emotional, dynamic voice.",
    "Hardboiled": "Dry, blunt, unsentimental.",
    "Poetic": "Figurative, flowing prose."
}

POVS = ["First Person", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]

# =========================
# HELPERS
# =========================
def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(new_chapter(parts[i], parts[i+1]))
    if not chapters:
        chapters.append(new_chapter("Chapter 1", text))
    return chapters

def new_chapter(title, text):
    return {
        "title": title.title(),
        "text": text.strip(),
        "outline": "",
        "workflow": "Draft",
        "versions": []
    }

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": ch["text"]
    })

def call_llm(system, prompt, temp):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def rewrite(text, settings):
    prompt = f"""
Rewrite the following text.

GENRE: {settings['genre']}
VOICE: {settings['voice']}
POV: {settings['pov']}
TENSE: {settings['tense']}
INTENSITY: {settings['intensity']}

TEXT:
{text}
"""
    return call_llm("You are a professional fiction editor.", prompt, settings["intensity"])

def outline(text, settings):
    prompt = f"""
Create a bullet-point outline.

GENRE: {settings['genre']}
VOICE: {settings['voice']}

TEXT:
{text}
"""
    return call_llm("You are a developmental editor.", prompt, 0.3)

# =========================
# SIDEBAR — PROJECTS
# =========================
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

    if st.session_state.current_project:
        upload = st.file_uploader("Import manuscript (.txt)", type=["txt"])
        if upload:
            text = upload.read().decode("utf-8")
            st.session_state.projects[st.session_state.current_project]["chapters"] = split_into_chapters(text)
            st.session_state.current_chapter = 0

# =========================
# MAIN GUARDS
# =========================
if not st.session_state.current_project:
    st.title("Olivetti")
    st.write("Create or select a project.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.warning("No chapters yet.")
    st.stop()

if st.session_state.current_chapter >= len(chapters):
    st.session_state.current_chapter = 0

chapter = chapters[st.session_state.current_chapter]

# =========================
# LAYOUT
# =========================
left, center, right = st.columns([1.2, 2.8, 2.2])

# LEFT — CHAPTER NAV
with left:
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"nav_{i}"):
            st.session_state.current_chapter = i

# CENTER — WRITING
with center:
    st.subheader("Draft")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    col1, col2 = st.columns(2)
    if col1.button("Save Version"):
        save_version(chapter)
    chapter["workflow"] = col2.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

# RIGHT — AI TOOLS
with right:
    st.subheader("AI Tools")

    genre = st.selectbox("Genre", list(GENRES.keys()))
    voice = st.selectbox("Voice", list(VOICES.keys()))
    pov = st.selectbox("POV", POVS)
    tense = st.selectbox("Tense", TENSES)
    intensity = st.slider("Intensity", 0.1, 1.0, 0.5)

    settings = {
        "genre": genre,
        "voice": voice,
        "pov": pov,
        "tense": tense,
        "intensity": intensity
    }

    st.divider()

    if st.button("Generate Outline"):
        chapter["outline"] = outline(chapter["text"], settings)

    chapter["outline"] = st.text_area("Outline", chapter["outline"], height=160)

    st.divider()

    if st.button("Rewrite (Preview)"):
        st.session_state.preview = rewrite(chapter["text"], settings)

    if "preview" in st.session_state:
        st.text_area("Preview", st.session_state.preview, height=200)
        if st.button("Apply Rewrite"):
            save_version(chapter)
            chapter["text"] = st.session_state.preview
            del st.session_state.preview

st.caption("Olivetti 20.1 — Recovery Desk")
