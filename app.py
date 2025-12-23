import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "lock_chapter": False,
        "preview_text": None,
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
            "text": parts[i + 1].strip(),
            "outline": "",
            "versions": [],
            "comments": []
        })

    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "outline": "",
            "versions": [],
            "comments": []
        })

    return chapters


def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })


def get_current():
    if not st.session_state.current_project:
        st.stop()

    project = st.session_state.projects.get(st.session_state.current_project)
    if not project or not project["chapters"]:
        st.warning("Import a manuscript to begin.")
        st.stop()

    idx = max(
        0,
        min(st.session_state.current_chapter, len(project["chapters"]) - 1)
    )
    st.session_state.current_chapter = idx
    return project, project["chapters"], project["chapters"][idx]


def call_llm(system, prompt, temperature=0.5):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return r.output_text


def ai_rewrite(mode, text):
    prompts = {
        "Rewrite": "Rewrite this chapter, preserving voice and intent.",
        "Tighten": "Tighten prose by removing redundancy and sharpening sentences.",
        "Tension": "Increase narrative tension and momentum.",
        "Clarity": "Clarify action, motivation, and cause-effect.",
        "Dialogue": "Polish dialogue for realism and subtext.",
        "Compress": "Reduce length by 15% without losing meaning."
    }

    prompt = f"""{prompts[mode]}

TEXT:
{text}
"""
    return call_llm(
        "You are a professional fiction editor.",
        prompt,
        temperature=0.55
    )

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("Projects")

    names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + names)

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

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti")
    st.write("Create or select a project to begin.")
    st.stop()

project, chapters, chapter = get_current()

# ============================================================
# LAYOUT
# ============================================================
left, center, right = st.columns([1.2, 3.2, 2])

# ---------------- LEFT ----------------
with left:
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i

    chapter["title"] = st.text_input("Chapter title", chapter["title"])
    st.session_state.lock_chapter = st.checkbox(
        "🔒 Lock Chapter",
        value=st.session_state.lock_chapter
    )

# ---------------- CENTER ----------------
with center:
    st.subheader("Draft")

    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=520,
        disabled=st.session_state.lock_chapter
    )

    if st.button("Save Version"):
        save_version(chapter)

    if st.session_state.preview_text:
        st.subheader("Preview (Not Applied)")
        st.text_area(
            "",
            st.session_state.preview_text,
            height=260
        )

        colA, colB = st.columns(2)
        if colA.button("Accept Rewrite"):
            save_version(chapter)
            chapter["text"] = st.session_state.preview_text
            st.session_state.preview_text = None

        if colB.button("Discard Preview"):
            st.session_state.preview_text = None

# ---------------- RIGHT ----------------
with right:
    st.subheader("AI Rewrite Suite")

    mode = st.selectbox(
        "Tool",
        ["Rewrite", "Tighten", "Tension", "Clarity", "Dialogue", "Compress"]
    )

    if st.button(
        "Run Tool",
        disabled=st.session_state.lock_chapter
    ):
        with st.spinner("Working…"):
            st.session_state.preview_text = ai_rewrite(
                mode,
                chapter["text"]
            )

st.caption("Olivetti 27.0 — AI Rewrite Suite")
