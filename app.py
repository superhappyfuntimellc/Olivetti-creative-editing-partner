import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 21.0")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "mode": "Writing"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# HELPERS
# ============================================================
def llm(system, prompt, temp=0.3):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def make_story_bible():
    return {
        "characters": "",
        "world": "",
        "timeline": "",
        "themes": "",
        "voice": ""
    }

def make_chapter(title, text):
    return {
        "title": title,
        "text": text,
        "workflow": "Draft",
        "status": "Needs Work",
        "notes": "",
        "snapshot": None,
        "versions": []
    }

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(make_chapter(parts[i].title(), parts[i+1].strip()))
    if not chapters:
        chapters.append(make_chapter("Chapter 1", text))
    return chapters

def save_snapshot(ch):
    ch["snapshot"] = ch["text"]
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def build_story_bible(text):
    prompt = f"""
Analyze the manuscript and extract a STORY BIBLE.

Return clearly labeled sections:

CHARACTERS:
- Name, role, traits, voice notes

WORLD / LORE:
- Setting rules, constraints

TIMELINE:
- Major events in order

THEMES:
- Core themes and motifs

VOICE:
- POV, tense, cadence, diction notes

Do not summarize the plot.
Do not rewrite prose.

MANUSCRIPT:
{text}
"""
    raw = llm(
        "You are a senior developmental editor building a canonical story bible.",
        prompt,
        0.3
    )

    sections = {
        "characters": "",
        "world": "",
        "timeline": "",
        "themes": "",
        "voice": ""
    }

    current = None
    for line in raw.splitlines():
        key = line.strip().lower()
        if key.startswith("characters"):
            current = "characters"
        elif key.startswith("world"):
            current = "world"
        elif key.startswith("timeline"):
            current = "timeline"
        elif key.startswith("themes"):
            current = "themes"
        elif key.startswith("voice"):
            current = "voice"
        elif current:
            sections[current] += line + "\n"

    return sections

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("Projects")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": make_story_bible()
            }
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

    if st.session_state.current_project:
        upload = st.file_uploader("Import manuscript (.txt)", type=["txt"])
        if upload:
            text = upload.read().decode("utf-8")
            project = st.session_state.projects[
                st.session_state.current_project
            ]
            project["chapters"] = split_into_chapters(text)

            with st.spinner("Building Story Bible…"):
                project["bible"] = build_story_bible(text)

    st.divider()
    st.radio(
        "Mode",
        ["Writing", "Editorial"],
        horizontal=True,
        key="mode"
    )

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 21.0")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]
bible = project["bible"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

ch = chapters[st.session_state.current_chapter]

left, center, right = st.columns([1.1, 3.4, 2.5])

# ============================================================
# LEFT — NAV
# ============================================================
with left:
    st.subheader("Chapters")
    for i, c in enumerate(chapters):
        if st.button(f"{i+1}. {c['title']}"):
            st.session_state.current_chapter = i

    ch["title"] = st.text_input("Title", ch["title"])

# ============================================================
# CENTER — WRITING
# ============================================================
with center:
    st.subheader("Chapter Text")

    c1, c2 = st.columns(2)
    if c1.button("Save Snapshot"):
        save_snapshot(ch)
    if c2.button("Undo Snapshot") and ch["snapshot"]:
        ch["text"] = ch["snapshot"]

    ch["text"] = st.text_area("", ch["text"], height=520)

# ============================================================
# RIGHT — STORY BIBLE (F1)
# ============================================================
with right:
    st.subheader("Story Bible")

    tab = st.selectbox(
        "Section",
        ["Characters", "World", "Timeline", "Themes", "Voice"]
    )

    key_map = {
        "Characters": "characters",
        "World": "world",
        "Timeline": "timeline",
        "Themes": "themes",
        "Voice": "voice"
    }

    k = key_map[tab]
    bible[k] = st.text_area(tab, bible[k], height=500)

st.caption("Olivetti 21.0 — Story Bible Engine")
