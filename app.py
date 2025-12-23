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
        "focus_mode": False,
        "show_tools": True,
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


def move_item(lst, i, direction):
    j = i + direction
    if 0 <= j < len(lst):
        lst[i], lst[j] = lst[j], lst[i]
        return j
    return i


def split_scenes(text):
    return [s for s in text.split("\n\n") if s.strip()]


def join_scenes(scenes):
    return "\n\n".join(scenes)


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
if st.session_state.focus_mode:
    left, center, right = st.columns([0.01, 5, 0.01])
else:
    left, center, right = st.columns([1.2, 3.2, 2])

# ---------------- LEFT — CHAPTER ORDER ----------------
if not st.session_state.focus_mode:
    with left:
        st.subheader("Chapters")
        for i, ch in enumerate(chapters):
            cols = st.columns([4, 1, 1])
            if cols[0].button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
                st.session_state.current_chapter = i
            if cols[1].button("↑", key=f"up_{i}"):
                st.session_state.current_chapter = move_item(chapters, i, -1)
            if cols[2].button("↓", key=f"down_{i}"):
                st.session_state.current_chapter = move_item(chapters, i, 1)

        chapter["title"] = st.text_input("Chapter title", chapter["title"])
        st.checkbox("🔒 Lock Chapter", key="lock_chapter")

# ---------------- CENTER — SCENE ORDER ----------------
with center:
    st.subheader("Draft")

    scenes = split_scenes(chapter["text"])
    for i, scene in enumerate(scenes):
        sc = st.columns([6, 1, 1])
        sc[0].write(scene[:200] + ("…" if len(scene) > 200 else ""))
        if sc[1].button("↑", key=f"scene_up_{i}"):
            scenes[i], scenes[i-1] = scenes[i-1], scenes[i]
        if sc[2].button("↓", key=f"scene_down_{i}") and i < len(scenes) - 1:
            scenes[i], scenes[i+1] = scenes[i+1], scenes[i]

    chapter["text"] = join_scenes(scenes)

    st.text_area(
        "",
        chapter["text"],
        height=420,
        disabled=st.session_state.lock_chapter
    )

    if st.button("Save Version"):
        save_version(chapter)

    if st.session_state.preview_text:
        st.subheader("Preview")
        st.text_area("", st.session_state.preview_text, height=240)

        colA, colB = st.columns(2)
        if colA.button("Accept Rewrite"):
            save_version(chapter)
            chapter["text"] = st.session_state.preview_text
            st.session_state.preview_text = None
        if colB.button("Discard Preview"):
            st.session_state.preview_text = None

# ---------------- RIGHT — AI ----------------
if st.session_state.show_tools and not st.session_state.focus_mode:
    with right:
        st.subheader("AI Rewrite Suite")

        mode = st.selectbox(
            "Tool",
            ["Rewrite", "Tighten", "Tension", "Clarity", "Dialogue", "Compress"]
        )

        if st.button("Run Tool", disabled=st.session_state.lock_chapter):
            with st.spinner("Working…"):
                st.session_state.preview_text = ai_rewrite(
                    mode,
                    chapter["text"]
                )

st.caption("Olivetti 29.0 — Structural Control")
