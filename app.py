import streamlit as st
import re
from datetime import datetime
from collections import Counter
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti 23.7", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "voice_bible": {},
        "analysis": [],
        "intensity": 0.5,
        "pov": "Close Third",
        "tense": "Past",
        "structure_locked": False,
        "instruction_bible": {
            "Editorial": "Revise for clarity and flow without changing voice.",
            "Minimal": "Make the smallest possible improvement.",
            "Aggressive": "Rewrite boldly for impact.",
            "Voice Locked": "Rewrite strictly matching the author’s voice."
        },
        "find_text": "",
        "replace_text": "",
        "case_sensitive": False,
        "regex_mode": False,
        "synonyms": []
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
            "text": parts[i+1].strip(),
            "workflow": "Draft",
            "versions": []
        })
    if not chapters:
        chapters.append({
            "title": "Chapter 1",
            "text": text,
            "workflow": "Draft",
            "versions": []
        })
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def split_scenes(text):
    return re.split(r"\n\s*(?:---|SCENE:)\s*\n", text)

def join_scenes(scenes):
    return "\n\n---\n\n".join(scenes)

def find_matches(text, pattern, case, regex):
    flags = 0 if case else re.IGNORECASE
    try:
        if regex:
            return list(re.finditer(pattern, text, flags))
        else:
            return list(re.finditer(re.escape(pattern), text, flags))
    except re.error:
        return []

def replace_all(text, pattern, repl, case, regex):
    flags = 0 if case else re.IGNORECASE
    if regex:
        return re.sub(pattern, repl, text, flags=flags)
    return re.sub(re.escape(pattern), repl, text, flags=flags)

def get_synonyms(word):
    prompt = f"Give 8 strong, context-neutral synonyms for the word '{word}'. One per line."
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return [w.strip("-• ") for w in r.output_text.splitlines() if w.strip()]

# ============================================================
# TOP BAR
# ============================================================
top = st.columns([2,2,2,2,2])
top[0].slider("Intensity", 0.0, 1.0, key="intensity")
top[1].selectbox("POV", ["First","Close Third","Omniscient"], key="pov")
top[2].selectbox("Tense", ["Past","Present"], key="tense")
top[3].toggle("Lock Structure", key="structure_locked")
top[4].button("Snapshot")

st.divider()

# ============================================================
# SIDEBAR — PROJECTS
# ============================================================
with st.sidebar:
    st.header("Projects")
    names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + names)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {"chapters": []}
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

    if not st.session_state.current_project:
        st.stop()

    project = st.session_state.projects[st.session_state.current_project]
    chapters = project["chapters"]

    st.divider()
    st.subheader("Chapters")
    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"ch_{i}"):
            st.session_state.current_chapter = i

# ============================================================
# MAIN
# ============================================================
chapter = chapters[st.session_state.current_chapter]

left, center, right = st.columns([1,3,2])

# ---------------- LEFT — SCENES ----------------
with left:
    st.subheader("Scenes")
    scenes = split_scenes(chapter["text"])
    for i, _ in enumerate(scenes):
        st.write(f"Scene {i+1}")
    chapter["text"] = join_scenes(scenes)

# ---------------- CENTER — EDITOR ----------------
with center:
    st.subheader("Chapter Text")
    chapter["title"] = st.text_input("Title", chapter["title"])
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    c1, c2 = st.columns(2)
    if c1.button("Save Version"):
        save_version(chapter)
    chapter["workflow"] = c2.selectbox(
        "Workflow",
        ["Draft","Revise","Polish","Final"],
        index=["Draft","Revise","Polish","Final"].index(chapter["workflow"])
    )

# ---------------- RIGHT — FIND / REPLACE / SYNONYMS ----------------
with right:
    st.subheader("Find & Replace")

    st.text_input("Find", key="find_text")
    st.text_input("Replace", key="replace_text")

    c1, c2 = st.columns(2)
    c1.checkbox("Case sensitive", key="case_sensitive")
    c2.checkbox("Regex", key="regex_mode")

    matches = []
    if st.session_state.find_text:
        matches = find_matches(
            chapter["text"],
            st.session_state.find_text,
            st.session_state.case_sensitive,
            st.session_state.regex_mode
        )
        st.caption(f"{len(matches)} matches")

    if st.button("Replace All") and matches:
        save_version(chapter)
        chapter["text"] = replace_all(
            chapter["text"],
            st.session_state.find_text,
            st.session_state.replace_text,
            st.session_state.case_sensitive,
            st.session_state.regex_mode
        )

    st.divider()
    st.subheader("Synonyms")

    word = st.text_input("Word for synonyms")
    if st.button("Suggest Synonyms") and word:
        st.session_state.synonyms = get_synonyms(word)

    for syn in st.session_state.synonyms:
        if st.button(syn):
            chapter["text"] = chapter["text"].replace(word, syn, 1)

st.caption("Olivetti 23.7 — Editorial Tools Restored")
