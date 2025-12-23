import streamlit as st
import re
from datetime import datetime
from collections import Counter
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti 23.9", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_chapter": 0,
        "intensity": 0.5,
        "analysis": [],
        "story_bible": {
            "pov": "Close Third",
            "tense": "Past",
            "style_rules": "",
            "characters": "",
            "setting": "",
            "themes": "",
            "prohibitions": ""
        },
        "instruction_bible": {
            "Editorial": "Revise for clarity and flow.",
            "Minimal": "Make the smallest possible improvement.",
            "Aggressive": "Rewrite boldly.",
            "Voice Locked": "Rewrite strictly matching the author’s voice."
        }
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# HELPERS
# ============================================================
def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def enforce_pov_tense(text):
    notes = []
    if st.session_state.story_bible["tense"] == "Past":
        if re.search(r"\bis\b|\bare\b", text):
            notes.append("Possible present-tense drift detected.")
    if st.session_state.story_bible["pov"] == "First":
        if re.search(r"\bhe\b|\bshe\b", text):
            notes.append("Possible POV drift detected (first person expected).")
    return notes

def ai_action(action, text, instruction):
    bible = st.session_state.story_bible
    prompt = f"""
ACTION: {action}

INSTRUCTIONS:
{instruction}

STORY BIBLE (MANDATORY):
POV: {bible['pov']}
TENSE: {bible['tense']}

STYLE RULES:
{bible['style_rules']}

CHARACTERS:
{bible['characters']}

SETTING:
{bible['setting']}

THEMES:
{bible['themes']}

PROHIBITIONS:
{bible['prohibitions']}

TEXT:
{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[{"role": "system", "content": "You are a professional novelist following strict canon rules."},
               {"role": "user", "content": prompt}],
        temperature=st.session_state.intensity
    )
    return r.output_text

# ============================================================
# TOP BAR
# ============================================================
top = st.columns([2,2,2])
top[0].slider("Intensity", 0.0, 1.0, key="intensity")
top[1].selectbox("POV", ["First","Close Third","Omniscient"], key="story_bible_pov")
top[2].selectbox("Tense", ["Past","Present"], key="story_bible_tense")

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

# ============================================================
# MAIN — STORY BIBLE + EDITOR
# ============================================================
project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]
chapter = chapters[st.session_state.current_chapter]

tabs = st.tabs(["Chapter", "Story Bible"])

# ---------------- CHAPTER ----------------
with tabs[0]:
    st.subheader("Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    if st.button("Save Version"):
        save_version(chapter)

    drift = enforce_pov_tense(chapter["text"])
    for d in drift:
        st.warning(d)

# ---------------- STORY BIBLE ----------------
with tabs[1]:
    sb = st.session_state.story_bible

    sb["pov"] = st.selectbox("Global POV", ["First","Close Third","Omniscient"], index=["First","Close Third","Omniscient"].index(sb["pov"]))
    sb["tense"] = st.selectbox("Global Tense", ["Past","Present"], index=["Past","Present"].index(sb["tense"]))

    sb["style_rules"] = st.text_area("Style Rules", sb["style_rules"], height=100)
    sb["characters"] = st.text_area("Characters", sb["characters"], height=120)
    sb["setting"] = st.text_area("Setting / World", sb["setting"], height=120)
    sb["themes"] = st.text_area("Themes & Motifs", sb["themes"], height=100)
    sb["prohibitions"] = st.text_area("Rules / Prohibitions", sb["prohibitions"], height=100)

st.caption("Olivetti 23.9 — Canon-Enforced Writing Engine")
