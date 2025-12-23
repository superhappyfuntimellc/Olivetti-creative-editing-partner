import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Olivetti 23.9",
    layout="wide",
)

client = OpenAI()

# =========================
# SESSION STATE INIT
# =========================
if "projects" not in st.session_state:
    st.session_state.projects = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

# =========================
# STYLE PRESETS
# =========================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit.",
    "Lyrical": "Rhythmic, image-driven, musical language.",
}

POVS = ["First", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]

# =========================
# HELPERS
# =========================
def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []

    for i in range(1, len(parts), 2):
        chapters.append({
            "title": parts[i].title(),
            "text": parts[i + 1].strip(),
            "outline": "",
            "versions": [],
        })

    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "outline": "",
            "versions": [],
        })

    return chapters


def save_version(chapter):
    chapter["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": chapter["text"],
    })


def get_current_chapter():
    if st.session_state.current_project is None:
        st.stop()

    project = st.session_state.projects.get(st.session_state.current_project)
    if not project:
        st.stop()

    chapters = project.get("chapters", [])
    if not chapters:
        st.warning("No chapters yet. Import a manuscript to begin.")
        st.stop()

    # Clamp index safely
    st.session_state.current_chapter = max(
        0, min(st.session_state.current_chapter, len(chapters) - 1)
    )

    return project, chapters, chapters[st.session_state.current_chapter]


def call_llm(system, prompt, temperature=0.3):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response.output_text


def generate_outline(text, genre, pov, tense, intensity):
    prompt = f"""
Create a concise chapter outline.

Rules:
- Bullet points only
- Major story beats
- No rewriting

Style:
Genre: {genre}
POV: {pov}
Tense: {tense}
Intensity: {intensity}

Chapter:
{text}
"""
    return call_llm(
        "You are a professional developmental editor.",
        prompt,
    )

# =========================
# SIDEBAR — PROJECTS
# =========================
with st.sidebar:
    st.header("Projects")

    projects = list(st.session_state.projects.keys())
    selection = st.selectbox("Project", ["— New —"] + projects)

    if selection == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {
                "chapters": [],
                "story_bible": "",
            }
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = selection

    if st.session_state.current_project:
        upload = st.file_uploader("Import manuscript (.txt)", type=["txt"])
        if upload:
            text = upload.read().decode("utf-8")
            st.session_state.projects[
                st.session_state.current_project
            ]["chapters"] = split_into_chapters(text)
            st.session_state.current_chapter = 0

# =========================
# MAIN
# =========================
if st.session_state.current_project is None:
    st.title("Olivetti 23.9")
    st.write("Create or select a project to begin.")
    st.stop()

project, chapters, chapter = get_current_chapter()

tabs = st.tabs(["Chapter", "Story Bible"])

# =========================
# TAB — CHAPTER
# =========================
with tabs[0]:
    left, center, right = st.columns([1.2, 3, 2])

    # LEFT — Chapter List
    with left:
        st.subheader("Chapters")
        for i, ch in enumerate(chapters):
            if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
                st.session_state.current_chapter = i

        chapter["title"] = st.text_input("Chapter title", chapter["title"])

    # CENTER — Writing
    with center:
        st.subheader("Draft")
        chapter["text"] = st.text_area(
            "",
            chapter["text"],
            height=520,
        )

        if st.button("Save Version"):
            save_version(chapter)

    # RIGHT — Tools
    with right:
        st.subheader("Tools")

        genre = st.selectbox("Genre", list(GENRES.keys()))
        pov = st.selectbox("POV", POVS)
        tense = st.selectbox("Tense", TENSES)
        intensity = st.slider("Intensity", 0.0, 1.0, 0.5)

        st.divider()
        st.subheader("Outline")

        if st.button("Generate Outline"):
            chapter["outline"] = generate_outline(
                chapter["text"],
                genre,
                pov,
                tense,
                intensity,
            )

        chapter["outline"] = st.text_area(
            "",
            chapter.get("outline", ""),
            height=220,
        )

# =========================
# TAB — STORY BIBLE
# =========================
with tabs[1]:
    st.subheader("Story Bible")
    project["story_bible"] = st.text_area(
        "Characters, world, rules, voice notes",
        project.get("story_bible", ""),
        height=500,
    )

st.caption("Olivetti 23.9 — Professional Authorial Core")
