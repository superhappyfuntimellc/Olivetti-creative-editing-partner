import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(layout="wide", page_title="Olivetti 20.8")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "mode": "Writing"  # Writing | Editorial
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# STYLE PRESETS
# ============================================================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit, lightness.",
    "Lyrical": "Rhythm, imagery, musical language."
}
POVS = ["First", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]

# ============================================================
# HELPERS
# ============================================================
def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(make_chapter(parts[i].title(), parts[i+1].strip()))
    if not chapters:
        chapters.append(make_chapter("Chapter 1", text))
    return chapters

def make_chapter(title, text):
    return {
        "title": title,
        "text": text,
        "workflow": "Draft",
        "status": "Needs Work",  # Needs Work | Solid | Final
        "notes": "",
        "versions": [],
        "snapshot": None,
        "preview": ""
    }

def save_snapshot(ch):
    ch["snapshot"] = ch["text"]
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def restore_snapshot(ch):
    if ch["snapshot"]:
        ch["text"] = ch["snapshot"]

def llm(system, prompt, temp=0.4):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

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

    st.divider()
    st.subheader("Mode")
    st.radio(
        "Editor Mode",
        ["Writing", "Editorial"],
        horizontal=True,
        key="mode"
    )

    st.divider()
    st.subheader("Voice Controls")
    genre = st.selectbox("Genre", list(GENRES.keys()))
    pov = st.selectbox("POV", POVS)
    tense = st.selectbox("Tense", TENSES)

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 20.8")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

if not chapters:
    st.write("Import a manuscript to begin.")
    st.stop()

ch = chapters[st.session_state.current_chapter]

left, center, right = st.columns([1.1, 3.4, 2.0])

# ============================================================
# LEFT — CHAPTER NAV + STATUS
# ============================================================
with left:
    st.subheader("Chapters")
    for i, c in enumerate(chapters):
        label = f"{i+1}. {c['title']} [{c['status']}]"
        if st.button(label, key=f"chap_{i}"):
            st.session_state.current_chapter = i

    ch["title"] = st.text_input("Title", ch["title"])
    ch["status"] = st.selectbox(
        "Status",
        ["Needs Work", "Solid", "Final"],
        index=["Needs Work", "Solid", "Final"].index(ch["status"])
    )

# ============================================================
# CENTER — WRITING + WORKFLOW BUTTONS
# ============================================================
with center:
    st.subheader("Chapter Text")

    # --- Workflow Buttons ---
    w1, w2, w3, w4 = st.columns(4)
    if w1.button("Save Snapshot"):
        save_snapshot(ch)
    if w2.button("Undo to Snapshot"):
        restore_snapshot(ch)
    if w3.button("Compare"):
        if ch["snapshot"]:
            st.info("Snapshot stored. Use Undo to restore.")
    if w4.button("Promote Stage"):
        stages = ["Draft", "Revise", "Polish", "Final"]
        idx = stages.index(ch["workflow"])
        if idx < len(stages) - 1:
            ch["workflow"] = stages[idx + 1]

    st.caption(f"Workflow Stage: {ch['workflow']}")

    ch["text"] = st.text_area(
        "",
        ch["text"],
        height=520
    )

# ============================================================
# RIGHT — EDITORIAL ACTIONS (ONLY IN EDITORIAL MODE)
# ============================================================
with right:
    st.subheader("Actions")

    if st.session_state.mode == "Writing":
        st.info("Writing Mode active.\nEditorial tools hidden.")

    else:
        action = st.selectbox(
            "Quick Action",
            [
                "Tighten Prose",
                "Clarify Action",
                "Reduce Adverbs",
                "Elevate Language",
                "Reset to Snapshot"
            ]
        )

        if action == "Reset to Snapshot":
            if st.button("Reset"):
                restore_snapshot(ch)

        else:
            if st.button("Preview"):
                ch["preview"] = llm(
                    "You are a senior fiction editor.",
                    f"{action}. Preserve voice.\n\nTEXT:\n{ch['text']}",
                    0.4
                )

            if ch.get("preview"):
                st.text_area("Preview", ch["preview"], height=240)
                if st.button("Accept"):
                    save_snapshot(ch)
                    ch["text"] = ch["preview"]
                    ch["preview"] = ""

        st.divider()
        st.subheader("Private Notes")
        ch["notes"] = st.text_area("Notes (non-AI)", ch["notes"], height=120)

st.caption("Olivetti 20.8 — Workflow Restored")
