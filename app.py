import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

st.set_page_config(layout="wide", page_title="🫒 Olivetti 19.1 — Tool Density")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
for k, v in {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "selected_para": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# TOOL PRESETS
# =========================
TOOLS = {
    "Rewrite": "Rewrite for clarity and flow without changing meaning.",
    "Expand": "Expand the moment with more sensory detail.",
    "Compress": "Tighten the prose, removing excess.",
    "Continue": "Continue naturally from the end.",
    "Dialogue Polish": "Improve dialogue realism and rhythm.",
    "Heighten Tension": "Increase suspense and emotional pressure.",
    "Make Colder": "Reduce warmth, increase distance or unease.",
    "Make Warmer": "Add intimacy and emotional warmth.",
    "Surprise": "Introduce an unexpected but fitting turn.",
    "Clarify": "Make meaning clearer without simplifying tone."
}

# =========================
# HELPERS
# =========================
def split_paragraphs(text):
    return [p for p in text.split("\n\n") if p.strip()]

def rebuild(paras):
    return "\n\n".join(paras)

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": ch["text"]
    })

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
            {"role": "system", "content": "You are a senior fiction editor who respects constraints."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return r.output_text

# =========================
# SIDEBAR — PROJECT
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
                "bible": "",
                "characters": {}
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
        "scene": {"pov": "", "location": "", "intent": ""},
        "versions": [],
        "outputs": []
    })

chapter = project["chapters"][st.session_state.current_chapter]
paragraphs = split_paragraphs(chapter["text"])

left, center, right = st.columns([1.1, 2.4, 2.5])

# =========================
# LEFT — PARAGRAPHS
# =========================
with left:
    st.subheader("¶ Target")
    for i, _ in enumerate(paragraphs):
        if st.button(f"¶ {i+1}", key=f"p{i}"):
            st.session_state.selected_para = i

# =========================
# CENTER — TEXT
# =========================
with center:
    st.subheader("✍️ Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    if st.button("💾 Save Version"):
        save_version(chapter)

# =========================
# RIGHT — TOOLS
# =========================
with right:
    st.subheader("🎯 Scope")
    scope = st.selectbox("Apply to", ["Paragraph", "Chapter"])

    st.divider()
    st.subheader("🔧 Tool Buttons")

    selected_tools = []
    for t in TOOLS:
        if st.checkbox(t):
            selected_tools.append(t)

    st.divider()
    st.subheader("🧠 Command Palette")
    command = st.text_input("Custom command (optional)")

    if st.button("Run Tools"):
        chapter["outputs"].clear()

        if scope == "Paragraph" and st.session_state.selected_para is not None:
            target = paragraphs[st.session_state.selected_para]
        else:
            target = chapter["text"]

        context = f"""
Story Bible:
{project['bible']}
"""

        for t in selected_tools:
            out = call_llm(context, TOOLS[t], target)
            chapter["outputs"].append({
                "label": t,
                "text": out,
                "scope": scope
            })

        if command:
            out = call_llm(context, command, target)
            chapter["outputs"].append({
                "label": f"Command: {command}",
                "text": out,
                "scope": scope
            })

    if chapter["outputs"]:
        st.divider()
        st.subheader("🧪 Outputs")

        for i, o in enumerate(chapter["outputs"]):
            with st.expander(o["label"], expanded=True):
                st.text_area("Preview", o["text"], height=160)

                if st.button("✅ Accept", key=f"a{i}"):
                    save_version(chapter)
                    if o["scope"] == "Paragraph" and st.session_state.selected_para is not None:
                        paragraphs[st.session_state.selected_para] = o["text"]
                        chapter["text"] = rebuild(paragraphs)
                    else:
                        chapter["text"] = o["text"]
                    chapter["outputs"].clear()
                    break

st.caption("🫒 Olivetti 19.1 — density without chaos")
