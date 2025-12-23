import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(
    layout="wide",
    page_title="🫒 Olivetti 19.7 — Authorial Mode"
)
client = OpenAI()

# =========================
# SESSION STATE
# =========================
defaults = {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "genre": "Literary",
    "pov": "Close Third",
    "tense": "Past",
    "style_sample": "",
    "voice_strictness": 0.4,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# AUTHORIAL PRESETS
# =========================
GENRES = {
    "Literary": "Elegant, interior, controlled prose.",
    "Commercial": "Clear, propulsive, accessible.",
    "Thriller": "Urgent, tense, fast-moving.",
    "Noir": "Hard-edged, cynical, concrete.",
    "Lyrical": "Musical language, imagery-forward."
}

POVS = [
    "First Person",
    "Close Third",
    "Omniscient"
]

TENSES = [
    "Past",
    "Present"
]

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
            "versions": [],
            "comments": []
        })

    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "versions": [],
            "comments": []
        })

    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

# =========================
# TOP — AUTHORIAL INTENT BAR
# =========================
st.markdown(
    """
    <style>
    .intent-bar {
        position: sticky;
        top: 0;
        z-index: 999;
        background: #111;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #333;
    }
    </style>
    """,
    unsafe_allow_html=True
)

with st.container():
    st.markdown('<div class="intent-bar">', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 1, 2.6])

    with c1:
        st.session_state.genre = st.selectbox(
            "Genre",
            list(GENRES.keys()),
            index=list(GENRES.keys()).index(st.session_state.genre)
        )

    with c2:
        st.session_state.pov = st.selectbox(
            "POV",
            POVS,
            index=POVS.index(st.session_state.pov)
        )

    with c3:
        st.session_state.tense = st.selectbox(
            "Tense",
            TENSES,
            index=TENSES.index(st.session_state.tense)
        )

    with c4:
        st.session_state.voice_strictness = st.slider(
            "Strictness",
            0.0, 1.0,
            st.session_state.voice_strictness,
            step=0.05
        )

    with c5:
        st.session_state.style_sample = st.text_input(
            "Match My Style (anchor sample)",
            st.session_state.style_sample,
            placeholder="Paste a paragraph that represents your ideal voice"
        )

    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# SIDEBAR — PROJECT NAV
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
# MAIN — FULL-SCREEN CANVAS
# =========================
if not st.session_state.current_project:
    st.title("🫒 Olivetti 19.7")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

nav, canvas, tools = st.columns([1.1, 4.5, 1.4])

# =========================
# LEFT — NAV
# =========================
with nav:
    st.subheader("📚 Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i
    chapter["title"] = st.text_input("Title", chapter["title"])

# =========================
# CENTER — WRITING CANVAS
# =========================
with canvas:
    st.subheader("✍️ Manuscript")
    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=650
    )

    if st.button("💾 Save Version"):
        save_version(chapter)

# =========================
# RIGHT — TOOLS / COMMENTS
# =========================
with tools:
    st.subheader("🧠 Tools")

    with st.expander("ℹ️ Current Intent", expanded=True):
        st.write(f"**Genre:** {st.session_state.genre}")
        st.write(f"**POV:** {st.session_state.pov}")
        st.write(f"**Tense:** {st.session_state.tense}")
        st.write(f"**Strictness:** {st.session_state.voice_strictness:.2f}")

    with st.expander("💬 Editor Comments"):
        if chapter["comments"]:
            for c in chapter["comments"]:
                st.info(c)
        else:
            st.caption("No comments yet.")

st.caption("🫒 Olivetti 19.7 — Full-Screen Authorial Mode")
