import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 21.2")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
if "projects" not in st.session_state:
    st.session_state.projects = {}
if "current_project" not in st.session_state:
    st.session_state.current_project = None
if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

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
        "voice": "",
        "pov": "Close Third",
        "tense": "Past"
    }

def make_chapter(title, text):
    return {
        "title": title,
        "text": text,
        "outline": "",
        "notes": "",
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

def build_story_bible(text):
    prompt = f"""
Extract a STORY BIBLE.

Return labeled sections only:
CHARACTERS
WORLD
TIMELINE
THEMES
VOICE
POV
TENSE

MANUSCRIPT:
{text}
"""
    raw = llm(
        "You are a senior developmental editor.",
        prompt,
        0.3
    )

    bible = make_story_bible()
    current = None
    for line in raw.splitlines():
        l = line.lower()
        if l.startswith("characters"):
            current = "characters"
        elif l.startswith("world"):
            current = "world"
        elif l.startswith("timeline"):
            current = "timeline"
        elif l.startswith("themes"):
            current = "themes"
        elif l.startswith("voice"):
            current = "voice"
        elif l.startswith("pov"):
            current = "pov"
        elif l.startswith("tense"):
            current = "tense"
        elif current:
            bible[current] += line + "\n"

    return bible

def update_chapters_outlines_pov_tense(full_text, bible, chapters):
    prompt = f"""
Using the STORY BIBLE as canon, update chapter titles
and generate outlines.

Also:
- Enforce POV: {bible['pov']}
- Enforce TENSE: {bible['tense']}
- Flag any POV or tense drift in outlines (do not rewrite prose)

Rules:
- Do NOT rewrite prose
- Do NOT delete chapters
- One outline per chapter

Return format:
CHAPTER 1 TITLE:
OUTLINE:

CHAPTER 2 TITLE:
OUTLINE:

STORY BIBLE:
{bible}

MANUSCRIPT:
{full_text}
"""
    raw = llm(
        "You are a developmental editor maintaining technical consistency.",
        prompt,
        0.3
    )

    blocks = re.split(r"CHAPTER\s+\d+ TITLE:", raw)[1:]
    for i, block in enumerate(blocks):
        if i >= len(chapters):
            break
        lines = block.strip().splitlines()
        if lines:
            chapters[i]["title"] = lines[0].strip()
            chapters[i]["outline"] = "\n".join(lines[1:]).strip()

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

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 21.2")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]
bible = project["bible"]

full_text = "\n\n".join(ch["text"] for ch in chapters)

left, center, right = st.columns([1.1, 3.4, 2.5])

# ============================================================
# LEFT — CHAPTERS
# ============================================================
with left:
    st.subheader("Chapters")
    for i, c in enumerate(chapters):
        if st.button(f"{i+1}. {c['title']}"):
            st.session_state.current_chapter = i

# ============================================================
# CENTER — WRITING
# ============================================================
ch = chapters[st.session_state.current_chapter]
with center:
    st.subheader(ch["title"])
    ch["text"] = st.text_area("", ch["text"], height=520)

# ============================================================
# RIGHT — STORY BIBLE + POV/TENSE
# ============================================================
with right:
    st.subheader("Story Bible")

    bible["pov"] = st.selectbox(
        "Point of View (Canonical)",
        ["First Person", "Close Third", "Distant Third", "Omniscient"],
        index=["First Person", "Close Third", "Distant Third", "Omniscient"].index(bible["pov"])
    )

    bible["tense"] = st.selectbox(
        "Tense (Canonical)",
        ["Past", "Present"],
        index=["Past", "Present"].index(bible["tense"])
    )

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

    bible[key_map[tab]] = st.text_area(
        tab, bible[key_map[tab]], height=260
    )

    st.divider()
    if st.button("Update Chapters, Outlines, POV & Tense"):
        with st.spinner("Synchronizing manuscript…"):
            update_chapters_outlines_pov_tense(
                full_text, bible, chapters
            )
        st.success("Chapters, outlines, POV, and tense synced.")

st.caption("Olivetti 21.2 — Canonical POV & Tense Control")
