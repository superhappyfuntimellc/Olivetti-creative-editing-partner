import streamlit as st
import re
from datetime import datetime
from openai import OpenAI
import statistics

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
        "focus_mode": False,
        "show_tools": True,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# ANALYSIS HELPERS
# ============================================================
def sentences(text):
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

def words(text):
    return re.findall(r"\b\w+\b", text.lower())

def dialogue_ratio(text):
    quoted = re.findall(r"\".*?\"", text, re.DOTALL)
    return len(" ".join(quoted)) / max(len(text), 1)

def analyze_text(text):
    sents = sentences(text)
    lens = [len(words(s)) for s in sents if words(s)]

    return {
        "sent_len_avg": statistics.mean(lens) if lens else 0,
        "sent_len_var": statistics.pstdev(lens) if len(lens) > 1 else 0,
        "dialogue_ratio": dialogue_ratio(text),
        "paragraphs": text.count("\n\n") + 1,
        "lexical_density": len(set(words(text))) / max(len(words(text)), 1),
    }

# ============================================================
# CORE HELPERS
# ============================================================
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

def get_current():
    if not st.session_state.current_project:
        st.stop()

    project = st.session_state.projects.get(st.session_state.current_project)
    if not project or not project["chapters"]:
        st.warning("Import a manuscript to begin.")
        st.stop()

    idx = max(0, min(st.session_state.current_chapter, len(project["chapters"]) - 1))
    st.session_state.current_chapter = idx
    return project, project["chapters"], project["chapters"][idx]

# ============================================================
# SIDEBAR
# ============================================================
if not st.session_state.focus_mode:
    with st.sidebar:
        st.header("Projects")

        names = list(st.session_state.projects.keys())
        choice = st.selectbox("Project", ["— New —"] + names)

        if choice == "— New —":
            name = st.text_input("Project name")
            if st.button("Create Project") and name:
                st.session_state.projects[name] = {
                    "chapters": [],
                    "voice_bible": None
                }
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

        st.divider()
        st.checkbox("Focus Mode", key="focus_mode")
        st.checkbox("Show Tools", key="show_tools")

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
    st.checkbox("🔒 Lock Chapter", key="lock_chapter")

# ---------------- CENTER ----------------
with center:
    st.subheader("Draft")
    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=560,
        disabled=st.session_state.lock_chapter
    )

    if st.button("Save Version"):
        save_version(chapter)

# ---------------- RIGHT — VOICE ----------------
with right:
    st.subheader("Voice Trainer")

    sample = st.text_area(
        "Paste your strongest work",
        height=180
    )

    if st.button("Train Voice"):
        project["voice_bible"] = analyze_text(sample)

    if project.get("voice_bible"):
        st.divider()
        st.subheader("Voice Bible")
        for k, v in project["voice_bible"].items():
            st.write(f"{k}: {round(v, 3)}")

        st.divider()
        st.subheader("Chapter Analysis")
        current = analyze_text(chapter["text"])

        for k in current:
            delta = current[k] - project["voice_bible"][k]
            st.write(f"{k}: {round(current[k],3)} (Δ {round(delta,3)})")

st.caption("Olivetti 30.0 — Voice Authority")
