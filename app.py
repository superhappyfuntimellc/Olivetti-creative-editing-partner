import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

st.set_page_config(layout="wide", page_title="🫒 Olivetti 18.4")
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
# PRESETS / TOOLS
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

TOOLS = {
    "Rewrite": "Rewrite the text while preserving meaning.",
    "Expand": "Expand the text with richer detail.",
    "Compress": "Condense the text without losing meaning.",
    "Clarify": "Make the text clearer and more precise.",
    "Heighten Tension": "Increase stakes and urgency.",
    "Continue": "Continue the text naturally."
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
            "workflow": "Draft",
            "versions": [],
            "outputs": [],
            "history": []
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "workflow": "Draft",
            "versions": [],
            "outputs": [],
            "history": []
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def call_llm(intent, text, style, bible):
    prompt = f"""
STORY BIBLE:
{bible}

STYLE:
{style}

INTENT:
{intent}

TEXT:
{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a professional fiction editor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return r.output_text

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
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": "",
                "presets": {}
            }
            st.session_state.current_project = name
    else:
        st.session_state.current_project = choice

    if st.session_state.current_project:
        upload = st.file_uploader("Import manuscript (.txt)", type=["txt"])
        if upload:
            text = upload.read().decode("utf-8")
            st.session_state.projects[
                st.session_state.current_project
            ]["chapters"] = split_into_chapters(text)

# =========================
# MAIN
# =========================
if not st.session_state.current_project:
    st.title("🫒 Olivetti Studio")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]
chapter = chapters[st.session_state.current_chapter]

left, center, right = st.columns([1.1, 2.4, 2.9])

# =========================
# LEFT
# =========================
with left:
    st.subheader("📚 Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}"):
            st.session_state.current_chapter = i
    chapter["title"] = st.text_input("Title", chapter["title"])

# =========================
# CENTER
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)
    if st.button("💾 Save Version"):
        save_version(chapter)

# =========================
# RIGHT
# =========================
with right:
    st.subheader("📘 Story Bible")
    project["bible"] = st.text_area("", project.get("bible", ""), height=110)

    st.subheader("🎯 Target")
    selection = st.text_area("Paragraph / sentence (optional)", height=90)
    target = selection.strip() if selection.strip() else chapter["text"]

    st.subheader("🎭 Style")
    genre = st.selectbox("Genre", GENRES.keys())
    voice = st.selectbox("Voice", VOICES.keys())
    style = f"{GENRES[genre]} {VOICES[voice]}"

    st.divider()
    st.subheader("🧰 Tools")
    for tool, intent in TOOLS.items():
        if st.button(tool):
            chapter["outputs"].append({
                "tool": tool,
                "target": target,
                "text": call_llm(intent, target, style, project["bible"])
            })

    if chapter["outputs"]:
        st.divider()
        st.subheader("🧪 Compare")
        for i, out in enumerate(chapter["outputs"]):
            st.markdown(f"### {out['tool']}")
            a, b = st.columns(2)
            with a:
                st.text_area("Original", out["target"], height=140, key=f"orig_{i}")
            with b:
                st.text_area("Proposed", out["text"], height=140, key=f"new_{i}")

            if st.button("✅ Accept Change", key=f"acc_{i}"):
                save_version(chapter)
                chapter["history"].append({
                    "time": datetime.now().strftime("%H:%M"),
                    "tool": out["tool"]
                })
                if selection.strip():
                    chapter["text"] = chapter["text"].replace(out["target"], out["text"], 1)
                else:
                    chapter["text"] = out["text"]
                chapter["outputs"].clear()
                break

    if chapter["history"]:
        st.divider()
        st.subheader("🧠 Recent")
        for h in reversed(chapter["history"][-5:]):
            st.caption(f"{h['time']} — {h['tool']}")

st.caption("🫒 Olivetti 18.4 — see the change before you choose")
