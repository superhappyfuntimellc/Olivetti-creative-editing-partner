import streamlit as st
import re
from datetime import datetime
from openai import OpenAI
import difflib

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Olivetti v13")
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

REVISION_MODES = {
    "Line Edit": "Improve clarity and flow. Do not add new content.",
    "Compress": "Cut redundancy. Reduce word count by ~15%.",
    "Sharpen Conflict": "Increase tension without changing events.",
    "Voice Consistency": "Align voice with the selected style."
}

# =========================
# HELPERS
# =========================
def normalize_chapter(ch):
    defaults = {
        "outline": "",
        "workflow": "Draft",
        "versions": [],
        "genre": "Literary",
        "voice": "Neutral Editor",
        "notes": "",
        "diagnostics": {}
    }
    for k, v in defaults.items():
        ch.setdefault(k, v)
    return ch

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(normalize_chapter({
            "title": parts[i].title(),
            "text": parts[i+1].strip()
        }))
    if not chapters:
        chapters.append(normalize_chapter({
            "title": "Chapter 1",
            "text": text
        }))
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

def generate_outline(ch):
    style = f"{GENRES[ch['genre']]} | {VOICES[ch['voice']]}"
    prompt = f"""
Create a concise chapter outline.
• Bullet points only
• Major story beats
• No rewriting

STYLE:
{style}

CHAPTER:
{ch['text']}
"""
    return call_llm("You are a professional developmental editor.", prompt)

def run_diagnostics(ch):
    prompt = f"""
Analyze this chapter. Do NOT rewrite.

Return:
• Scene purpose (1 sentence)
• What changes from start → end
• Pacing issues (if any)
• Redundant beats
• One concrete revision priority

CHAPTER:
{ch['text']}
"""
    return call_llm("You are a senior developmental editor.", prompt)

def revise_text(ch, mode):
    instruction = REVISION_MODES[mode]
    prompt = f"""
{instruction}

Maintain genre and voice.

GENRE: {ch['genre']}
VOICE: {ch['voice']}

TEXT:
{ch['text']}
"""
    return call_llm("You are a professional line editor.", prompt, temp=0.4)

def diff_text(old, new):
    diff = difflib.ndiff(old.splitlines(), new.splitlines())
    formatted = []
    for line in diff:
        if line.startswith("+ "):
            formatted.append(f"➕ {line[2:]}")
        elif line.startswith("- "):
            formatted.append(f"➖ {line[2:]}")
        elif line.startswith("? "):
            continue
        else:
            formatted.append(f"  {line[2:]}")
    return "\n".join(formatted)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("📁 Projects")
    choice = st.selectbox("Project", ["— New —"] + list(st.session_state.projects.keys()))

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
    st.title("🫒 Olivetti v13")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

idx = st.session_state.current_chapter
chapter = chapters[idx]

left, center, right = st.columns([1.1, 2.4, 2.5])

# =========================
# LEFT — CHAPTER NAV
# =========================
with left:
    st.subheader("📚 Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']} ({ch['workflow']})", key=f"chap_{i}"):
            st.session_state.current_chapter = i
    chapter["title"] = st.text_input("Chapter title", chapter["title"])

# =========================
# CENTER — TEXT
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    c1, c2 = st.columns(2)
    if c1.button("💾 Save Version"):
        save_version(chapter)

    chapter["workflow"] = c2.selectbox(
        "Workflow Stage",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )

    st.divider()
    st.subheader("🛠 Revision Mode")
    mode = st.selectbox("Edit Type", list(REVISION_MODES.keys()))
    if st.button("Apply Revision"):
        save_version(chapter)
        chapter["text"] = revise_text(chapter, mode)

# =========================
# RIGHT — EDITORIAL + DIFF
# =========================
with right:
    st.subheader("🎭 Style")
    chapter["genre"] = st.selectbox("Genre", list(GENRES.keys()),
        index=list(GENRES.keys()).index(chapter["genre"]))
    chapter["voice"] = st.selectbox("Voice", list(VOICES.keys()),
        index=list(VOICES.keys()).index(chapter["voice"]))

    st.divider()
    st.subheader("📑 Outline")
    if st.button("Generate Outline"):
        chapter["outline"] = generate_outline(chapter)
    st.text_area("", chapter["outline"], height=150)

    st.divider()
    st.subheader("🧠 Diagnostics")
    if st.button("Run Diagnostics"):
        chapter["diagnostics"]["developmental"] = run_diagnostics(chapter)
    st.text_area("", chapter["diagnostics"].get("developmental", ""), height=160)

    st.divider()
    st.subheader("🧾 Version Diff")
    if chapter["versions"]:
        labels = [v["time"] for v in chapter["versions"]]
        sel = st.selectbox("Compare with version", labels)
        old = next(v["text"] for v in chapter["versions"] if v["time"] == sel)
        st.text_area("Diff (➕ added / ➖ removed)", diff_text(old, chapter["text"]), height=220)
    else:
        st.caption("No saved versions yet.")

st.caption("Olivetti v13 — Write with history, revise without fear")
