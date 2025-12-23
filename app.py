import streamlit as st
from datetime import datetime
from openai import OpenAI
import re

st.set_page_config(layout="wide", page_title="🫒 Olivetti 19.3 — Dialogue & Scene Intelligence")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
for k, v in {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "selection": "",
    "stack_base": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# TOOLS
# =========================
TOOLS = {
    "Dialogue Polish": "Improve dialogue realism, subtext, and rhythm.",
    "Remove On-the-Nose": "Remove obvious or blunt dialogue lines.",
    "Heighten Tension": "Increase tension without melodrama.",
    "Clarify": "Clarify meaning while preserving voice.",
    "Rewrite": "Rewrite cleanly without changing intent."
}

BEATS = ["Setup", "Escalation", "Turn", "Aftermath"]

# =========================
# HELPERS
# =========================
def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": ch["text"]
    })

def is_dialogue(line):
    return bool(re.search(r'^".*"$', line.strip()))

def filter_text(text, mode):
    lines = text.split("\n")
    if mode == "Dialogue only":
        return "\n".join([l for l in lines if is_dialogue(l)])
    if mode == "Narration only":
        return "\n".join([l for l in lines if not is_dialogue(l)])
    return text

def call_llm(context, intent, text):
    prompt = f"""
CONTEXT:
{context}

INTENT:
{intent}

TEXT:
{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a senior fiction editor. Respect voice and constraints."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return r.output_text

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("📁 Project")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": ""
            }
            st.session_state.current_project = name
    else:
        st.session_state.current_project = choice

    project = st.session_state.projects.get(st.session_state.current_project)

    if project:
        st.divider()
        st.subheader("📘 Story Bible")
        project["bible"] = st.text_area("", project["bible"], height=120)

# =========================
# MAIN
# =========================
if not project:
    st.title("🫒 Olivetti Studio")
    st.stop()

if not project["chapters"]:
    project["chapters"].append({
        "title": "Chapter 1",
        "text": "",
        "versions": [],
        "beats": {},
        "outputs": []
    })

chapter = project["chapters"][st.session_state.current_chapter]

left, center, right = st.columns([1.1, 2.6, 2.7])

# =========================
# CENTER — TEXT
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    if st.button("💾 Save Version"):
        save_version(chapter)

# =========================
# RIGHT — INTELLIGENCE
# =========================
with right:
    st.subheader("🎯 Scope")
    scope = st.selectbox("Apply to", ["Selection", "Chapter"])

    st.subheader("🎭 Text Type")
    text_mode = st.selectbox(
        "Affect",
        ["All", "Dialogue only", "Narration only"]
    )

    st.divider()
    st.subheader("🎬 Scene Beat")
    beat = st.selectbox("Current beat", BEATS)

    st.divider()
    st.subheader("🔧 Tools")
    chosen = st.multiselect("Choose tools", list(TOOLS.keys()))

    if st.button("Run"):
        chapter["outputs"].clear()

        base = st.session_state.stack_base or chapter["text"]
        filtered = filter_text(base, text_mode)

        context = f"""
Story Bible:
{project['bible']}

Scene Beat:
{beat}
"""

        current = filtered
        for t in chosen:
            current = call_llm(context, TOOLS[t], current)

        chapter["outputs"].append({
            "before": filtered,
            "after": current
        })

    if chapter["outputs"]:
        st.divider()
        st.subheader("🧾 Compare")

        out = chapter["outputs"][0]
        a, b = st.columns(2)
        with a:
            st.text_area("Before", out["before"], height=180)
        with b:
            st.text_area("After", out["after"], height=180)

        if st.button("➕ Stack Another Tool"):
            st.session_state.stack_base = out["after"]

        if st.button("✅ Accept"):
            save_version(chapter)
            chapter["text"] = chapter["text"].replace(out["before"], out["after"])
            chapter["outputs"].clear()
            st.session_state.stack_base = None

st.caption("🫒 Olivetti 19.3 — dialogue-aware, scene-aware editing")
