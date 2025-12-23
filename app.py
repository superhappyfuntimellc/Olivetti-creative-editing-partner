import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(layout="wide", page_title="Olivetti Studio")
client = OpenAI()

# =========================================================
# SESSION STATE
# =========================================================
if "projects" not in st.session_state:
    st.session_state.projects = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

# =========================================================
# STYLE PRESETS
# =========================================================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit.",
    "Lyrical": "Musical language, imagery, rhythm.",
}

VOICES = {
    "Neutral Editor": "Clear, professional, invisible.",
    "Minimal": "Short sentences. Subtext.",
    "Expressive": "Emotion-forward.",
    "Hardboiled": "Dry, blunt, unsentimental.",
    "Poetic": "Figurative, evocative.",
}

TOOLS = [
    "Rewrite",
    "Expand",
    "Compress",
    "Continue",
    "Shift POV",
    "Shift Tense",
]

# =========================================================
# HELPERS
# =========================================================
def new_chapter(title, text):
    return {
        "title": title,
        "text": text,
        "notes": "",
        "locked": False,
        "workflow": "Draft",
        "versions": [],
        "outputs": {tool: [] for tool in TOOLS},
    }

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(new_chapter(parts[i].title(), parts[i+1].strip()))
    if not chapters:
        chapters.append(new_chapter("Chapter 1", text))
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def call_llm(system, prompt, temp=0.4):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def run_tool(tool, text, genre, voice, sample):
    style = f"{GENRES[genre]} {VOICES[voice]}"
    if sample:
        style += f"\nMatch this style:\n{sample}"

    prompt = f"""
TOOL: {tool}

STYLE:
{style}

TEXT:
{text}
"""
    return call_llm("You are a professional fiction editor.", prompt)

# =========================================================
# SIDEBAR — PROJECTS
# =========================================================
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

# =========================================================
# MAIN
# =========================================================
if not st.session_state.current_project:
    st.title("🫒 Olivetti Studio")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

idx = st.session_state.current_chapter
chapter = chapters[idx]

left, center, right = st.columns([1.3, 3.2, 2.7])

# =========================================================
# LEFT — STRUCTURE
# =========================================================
with left:
    st.subheader("📚 Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i

    chapter["title"] = st.text_input("Title", chapter["title"])
    chapter["workflow"] = st.selectbox(
        "Workflow",
        ["Draft", "Revise", "Polish", "Final"],
        index=["Draft", "Revise", "Polish", "Final"].index(chapter["workflow"])
    )
    chapter["locked"] = st.checkbox("🔒 Lock chapter", value=chapter["locked"])

# =========================================================
# CENTER — WRITING
# =========================================================
with center:
    st.subheader("✍️ Chapter Text")

    if chapter["locked"]:
        st.text_area("", chapter["text"], height=400, disabled=True)
    else:
        chapter["text"] = st.text_area("", chapter["text"], height=400)

    st.subheader("📝 Chapter Notes")
    chapter["notes"] = st.text_area("", chapter["notes"], height=120)

# =========================================================
# RIGHT — TOOLS + OUTPUTS
# =========================================================
with right:
    st.subheader("🧰 Tools")

    genre = st.selectbox("Genre", list(GENRES.keys()))
    voice = st.selectbox("Voice", list(VOICES.keys()))
    sample = st.text_area("Style Sample (optional)", height=70)

    for tool in TOOLS:
        if st.button(tool):
            if chapter["locked"]:
                st.warning("Chapter is locked.")
            else:
                with st.spinner(f"{tool}…"):
                    output = run_tool(tool, chapter["text"], genre, voice, sample)
                    chapter["outputs"][tool].insert(0, {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "text": output
                    })

    st.divider()
    st.subheader("🪞 Outputs (by Tool)")

    for tool, outputs in chapter["outputs"].items():
        if outputs:
            with st.expander(f"{tool} ({len(outputs)})", expanded=False):
                for i, out in enumerate(outputs):
                    st.caption(out["time"])
                    st.text_area("", out["text"], height=160, key=f"{tool}_{i}")

                    col1, col2 = st.columns(2)
                    if col1.button("✅ Accept", key=f"acc_{tool}_{i}"):
                        save_version(chapter)
                        chapter["text"] = out["text"]
                        chapter["outputs"] = {t: [] for t in TOOLS}
                        st.experimental_rerun()

                    if col2.button("❌ Reject", key=f"rej_{tool}_{i}"):
                        outputs.pop(i)
                        st.experimental_rerun()

st.caption("Olivetti Studio — independent tools, deliberate choice")
