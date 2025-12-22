import streamlit as st
import os
from openai import OpenAI

# Prevent file watcher crash
os.environ["STREAMLIT_WATCH_FILES"] = "false"

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🫒 Olivetti — Writing Workspace v5.0")

client = OpenAI()

# ================== STATE ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "My First Novel": {
            "chapters": {},
            "order": []
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
    blocks = text.split("\n\n")
    for i, block in enumerate(blocks, start=1):
        name = f"Chapter {i}"
        chapters[name] = block.strip()
        order.append(name)
    return chapters, order

def ai_action(text, action, style, tense):
    prompt = f"""
You are a professional novelist.

ACTION: {action}
STYLE: {style}
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
        projects[new_project] = {"chapters": {}, "order": []}
        st.session_state.active_project = new_project
        st.session_state.active_chapter = None

    st.selectbox(
        "Active Project",
        list(projects.keys()),
        key="active_project"
    )

    st.divider()
    st.header("📄 Import Manuscript")

    uploaded = st.file_uploader("Upload .txt manuscript", type=["txt"])
    if uploaded:
        text = uploaded.read().decode("utf-8")
        chapters, order = split_into_chapters(text)
        project["chapters"] = chapters
        project["order"] = order
        st.session_state.active_chapter = order[0]
        st.success("Manuscript imported.")

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
        project["chapters"][chap] = text  # autosave
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
        ["Neutral", "Noir", "Lyrical", "Comedy", "Thriller", "Ironic"]
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
        with st.spinner("Working..."):
            st.session_state.ai_result = ai_action(
                source_text, action, style, tense
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
