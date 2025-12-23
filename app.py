import streamlit as st
from datetime import datetime
from openai import OpenAI

st.set_page_config(layout="wide", page_title="🫒 Olivetti 19.2 — Precision Mode")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
for k, v in {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "selection": ""
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# TOOLS
# =========================
TOOLS = {
    "Rewrite": "Rewrite clearly without changing meaning.",
    "Expand": "Expand with sensory detail.",
    "Compress": "Tighten prose aggressively.",
    "Dialogue Polish": "Improve dialogue realism.",
    "Heighten Tension": "Increase suspense and unease.",
    "Clarify": "Clarify meaning without simplifying voice.",
    "Surprise": "Add an unexpected but fitting turn."
}

# =========================
# HELPERS
# =========================
def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": ch["text"]
    })

def call_llm(context, intent, text, avoid=""):
    prompt = f"""
CONTEXT:
{context}

PREVIOUS APPROACH TO AVOID:
{avoid}

INTENT:
{intent}

TEXT:
{text}
"""
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a senior fiction editor. Respect constraints. Avoid repetition."},
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
        "memory": {},
        "outputs": []
    })

chapter = project["chapters"][st.session_state.current_chapter]

left, center, right = st.columns([1.2, 2.6, 2.6])

# =========================
# CENTER — TEXT + SELECTION
# =========================
with center:
    st.subheader("✍️ Chapter Text")

    chapter["text"] = st.text_area(
        "Edit text (you can select text below)",
        chapter["text"],
        height=520
    )

    st.caption("Highlight text to enable Selection scope")

    if st.button("💾 Save Version"):
        save_version(chapter)

# =========================
# RIGHT — TOOLS + DIFF
# =========================
with right:
    st.subheader("🎯 Scope")
    scope = st.selectbox(
        "Apply to",
        ["Selection", "Paragraph", "Chapter"]
    )

    st.divider()
    st.subheader("🔧 Tools")

    selected = st.multiselect("Choose tools", list(TOOLS.keys()))

    if st.button("Run"):
        chapter["outputs"].clear()

        target = (
            st.session_state.selection
            if scope == "Selection" and st.session_state.selection
            else chapter["text"]
        )

        avoid = chapter["memory"].get(target, "")

        context = f"Story Bible:\n{project['bible']}"

        for t in selected:
            out = call_llm(context, TOOLS[t], target, avoid)
            chapter["outputs"].append({
                "tool": t,
                "before": target,
                "after": out
            })

    if chapter["outputs"]:
        st.divider()
        st.subheader("🧾 Diff View")

        for i, o in enumerate(chapter["outputs"]):
            with st.expander(o["tool"], expanded=True):
                a, b = st.columns(2)
                with a:
                    st.text_area("Before", o["before"], height=140)
                with b:
                    st.text_area("After", o["after"], height=140)

                if st.button("✅ Accept", key=f"acc{i}"):
                    save_version(chapter)
                    chapter["text"] = chapter["text"].replace(o["before"], o["after"])
                    chapter["memory"][o["before"]] = o["tool"]
                    chapter["outputs"].clear()
                    break

st.caption("🫒 Olivetti 19.2 — precision over noise")
