import streamlit as st
import os
from openai import OpenAI

# Prevent Streamlit watcher crash
os.environ["STREAMLIT_WATCH_FILES"] = "false"

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🫒 Olivetti — Writing Workspace v6.0")

client = OpenAI()

# ================== STATE ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "My First Novel": {
            "chapters": {},
            "order": [],
            "style_samples": ""
        }
    }

if "active_project" not in st.session_state:
    st.session_state.active_project = "My First Novel"

if "active_chapter" not in st.session_state:
    st.session_state.active_chapter = None

if "ai_result" not in st.session_state:
    st.session_state.ai_result = ""

projects = st.session_state.projects
project = projects[st.session_state.active_project]

# ================== HELPERS ==================
def split_into_chapters(text):
    chapters = {}
    order = []
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    for i, block in enumerate(blocks, start=1):
        name = f"Chapter {i}"
        chapters[name] = block
        order.append(name)
    return chapters, order

def ai_action(text, action, style, tense, style_samples):
    style_block = ""
    if style == "Match My Writing Style" and style_samples.strip():
        style_block = f"""
You must closely match the following author's writing style.
Analyze sentence length, rhythm, diction, tone, and narrative distance.

AUTHOR STYLE SAMPLES:
{style_samples}
"""

    prompt = f"""
You are a professional novelist and editor.

{style_block}

ACTION: {action}
STYLE MODE: {style}
TENSE: {tense}

TEXT:
{text}
"""
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0.7
    )
    return response.output_text

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    new_project = st.text_input("New project name")
    if st.button("➕ Create Project") and new_project:
        projects[new_project] = {
            "chapters": {},
            "order": [],
            "style_samples": ""
        }
        st.session_state.active_project = new_project
        st.session_state.active_chapter = None

    st.selectbox(
        "Active Project",
        list(projects.keys()),
        key="active_project"
    )

    st.divider()
    st.header("🧬 Writing Style Training")

    st.caption("Paste 1–3 samples of *your own writing*")
    project["style_samples"] = st.text_area(
        "Style Samples (saved automatically)",
        value=project.get("style_samples", ""),
        height=200
    )

    if project["style_samples"].strip():
        st.success("Style locked for this project")

    st.divider()
    st.header("📄 Import Manuscript")

    uploaded = st.file_uploader("Upload .txt manuscript", type=["txt"])
    if uploaded:
        text = uploaded.read().decode("utf-8")
        chapters, order = split_into_chapters(text)
        project["chapters"] = chapters
        project["order"] = order
        st.session_state.active_chapter = order[0]
        st.success("Manuscript imported and split.")

    st.divider()
    st.header("📚 Chapters")

    for name in project["order"]:
        if st.button(name, key=f"chap_{name}"):
            st.session_state.active_chapter = name

# ================== LAYOUT ==================
left, center, right = st.columns([1, 3, 2])

# ================== NAV ==================
with left:
    st.subheader("🧭 Navigator")
    for i, name in enumerate(project["order"]):
        st.write(f"{i+1}. {name}")

# ================== EDITOR ==================
with center:
    st.subheader("✍️ Writing")

    if st.session_state.active_chapter:
        chap = st.session_state.active_chapter
        text = st.text_area(
            chap,
            value=project["chapters"].get(chap, ""),
            height=600
        )
        project["chapters"][chap] = text
        st.caption("✔ Autosaved")

    else:
        st.info("Select or import a chapter.")

# ================== AI PANEL ==================
with right:
    st.subheader("🤖 AI Tools")

    action = st.selectbox(
        "Action",
        ["Rewrite", "Expand", "Tighten", "Change Tense"]
    )

    style = st.selectbox(
        "Style",
        [
            "Neutral",
            "Noir",
            "Lyrical",
            "Comedy",
            "Thriller",
            "Ironic",
            "Match My Writing Style"
        ]
    )

    tense = st.selectbox(
        "Tense",
        ["Preserve", "Past", "Present"]
    )

    use_selection = st.checkbox("Use selected text (manual paste)")

    source_text = ""
    if use_selection:
        source_text = st.text_area("Paste selection here", height=150)
    elif st.session_state.active_chapter:
        source_text = project["chapters"][st.session_state.active_chapter]

    if st.button("✨ Run AI") and source_text.strip():
        with st.spinner("Writing in your voice…"):
            st.session_state.ai_result = ai_action(
                source_text,
                action,
                style,
                tense,
                project.get("style_samples", "")
            )

    if st.session_state.ai_result:
        st.text_area(
            "AI Output (review before applying)",
            st.session_state.ai_result,
            height=300
        )

        if st.button("⬅ Replace Chapter Text"):
            if st.session_state.active_chapter:
                project["chapters"][st.session_state.active_chapter] = st.session_state.ai_result
                st.session_state.ai_result = ""
