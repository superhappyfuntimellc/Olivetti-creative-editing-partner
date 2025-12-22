import streamlit as st
import os

# Disable file watching (prevents inotify crash)
os.environ["STREAMLIT_WATCH_FILES"] = "false"

# ================== APP SETUP ==================
st.set_page_config(layout="wide")
st.title("🫒 Olivetti — Interactive Manuscript Workspace (v4.0)")

# ================== STATE INIT ==================
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

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_names = list(projects.keys())
    new_project = st.text_input("New project name")

    if st.button("➕ Create Project") and new_project:
        projects[new_project] = {"chapters": {}, "order": []}
        st.session_state.active_project = new_project
        st.session_state.active_chapter = None

    st.divider()

    st.selectbox(
        "Active Project",
        project_names,
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
        st.session_state.active_chapter = order[0] if order else None
        st.success("Manuscript imported and split into chapters.")

    st.divider()
    st.header("📚 Chapters")

    for name in project["order"]:
        if st.button(name, key=f"chap_{name}"):
            st.session_state.active_chapter = name

# ================== MAIN LAYOUT ==================
left, right = st.columns([1, 3])

# ================== CHAPTER NAV ==================
with left:
    st.subheader("🧭 Chapter Navigator")

    if project["order"]:
        for idx, name in enumerate(project["order"]):
            st.write(f"{idx+1}. {name}")

        st.divider()

        if st.session_state.active_chapter:
            new_name = st.text_input(
                "Rename chapter",
                value=st.session_state.active_chapter
            )

            if st.button("✏️ Rename"):
                if new_name not in project["chapters"]:
                    content = project["chapters"].pop(st.session_state.active_chapter)
                    project["chapters"][new_name] = content
                    index = project["order"].index(st.session_state.active_chapter)
                    project["order"][index] = new_name
                    st.session_state.active_chapter = new_name

        st.divider()

        move_up = st.button("⬆ Move Up")
        move_down = st.button("⬇ Move Down")

        if st.session_state.active_chapter:
            idx = project["order"].index(st.session_state.active_chapter)
            if move_up and idx > 0:
                project["order"][idx], project["order"][idx-1] = (
                    project["order"][idx-1],
                    project["order"][idx]
                )
            if move_down and idx < len(project["order"]) - 1:
                project["order"][idx], project["order"][idx+1] = (
                    project["order"][idx+1],
                    project["order"][idx]
                )

# ================== CHAPTER EDITOR ==================
with right:
    st.subheader("✍️ Chapter Editor")

    if st.session_state.active_chapter:
        chapter = st.session_state.active_chapter

        content = st.text_area(
            label=f"Editing: {chapter}",
            value=project["chapters"].get(chapter, ""),
            height=600
        )

        # Autosave
        project["chapters"][chapter] = content

        st.caption("✔ Autosaved")

    else:
        st.info("Import a manuscript or select a chapter to begin.")
