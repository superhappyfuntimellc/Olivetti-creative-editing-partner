import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Olivetti")
client = OpenAI()

# =========================
# SESSION STATE
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
    "Comedy": "Timing, irony, wit, lightness.",
    "Lyrical": "Rhythm, imagery, musical language.",
    "Ironic": "Detached, sharp, understated humor."
}

VOICES = {
    "Neutral Editor": "Clear, professional, invisible style.",
    "Minimal": "Short sentences. Subtext. Restraint.",
    "Expressive": "Emotion-forward, dynamic voice.",
    "Hardboiled": "Dry, blunt, unsentimental.",
    "Poetic": "Figurative, flowing, evocative."
}

# =========================
# HELPERS
# =========================
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

def call_llm(system, prompt, temp=0.3):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def generate_outline(text, genre, voice, sample):
    style = f"Genre: {GENRES[genre]}\nVoice: {VOICES[voice]}"
    if sample:
        style += f"\nMatch this style:\n{sample}"

    prompt = f"""
Create a concise chapter outline.
• Bullet points only
• Major beats
• No rewriting

STYLE:
{style}

CHAPTER:
{text}
"""
    return call_llm("You are a professional developmental editor.", prompt)

def rewrite_text(text, genre, voice, sample):
    style = f"{GENRES[genre]} {VOICES[voice]}"
    if sample:
        style += f"\nMatch this style:\n{sample}"

    prompt = f"""
Rewrite this chapter using the style below.

STYLE:
{style}

TEXT:
{text}
"""
    return call_llm("You are a professional fiction editor.", prompt, 0.5)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("📁 Projects")

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
if not st.session_state.current_project:
    st.title("🫒 Olivetti")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

left, center, right = st.columns([1.2, 2.8, 2.2])

# =========================
# LEFT — CHAPTERS
# =========================
with left:
    st.subheader("📚 Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i
    chapter["title"] = st.text_input("Chapter title", chapter["title"])

# =========================
# CENTER — WRITING
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    col1, col2 = st.columns(2)
    if col1.button("💾 Save Version"):
        save_version(chapter)

    chapter["workflow"] = col2.selectbox(
        "Workflow Stage",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

# =========================
# RIGHT — STYLE + PLAY
# =========================
with right:
    st.subheader("🎭 Style Playground")

    genre = st.selectbox("Genre", list(GENRES.keys()))
    voice = st.selectbox("Voice", list(VOICES.keys()))
    sample = st.text_area("Match My Writing Style (optional)", height=120)

    st.divider()
    st.subheader("📑 Outline")

    if st.button("Generate Outline"):
        chapter["outline"] = generate_outline(
            chapter["text"], genre, voice, sample
        )

    chapter["outline"] = st.text_area("", chapter["outline"], height=180)

    st.divider()
    st.subheader("🧪 Rewrite Playground")

    if st.button("Rewrite Chapter (Preview)"):
        with st.spinner("Rewriting…"):
            chapter["preview"] = rewrite_text(
                chapter["text"], genre, voice, sample
            )

    if "preview" in chapter:
        st.text_area("Preview", chapter["preview"], height=200)
        if st.button("✅ Accept Rewrite"):
            save_version(chapter)
            chapter["text"] = chapter.pop("preview")

st.caption("Olivetti — Built to explore, not just finish")
