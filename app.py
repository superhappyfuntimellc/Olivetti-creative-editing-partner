import streamlit as st

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("Olivetti — Manuscript Studio (Workflow Edition)")

# ================== SESSION STATE ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "New Project": {
            "story_bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world_rules": "",
                "characters": []
            },
            "outline": "",
            "chapters": {
                "Chapter 1": {
                    "text": "",
                    "status": "Draft"
                }
            }
        }
    }

if "current_project" not in st.session_state:
    st.session_state.current_project = "New Project"

projects = st.session_state.projects
project = projects[st.session_state.current_project]

WORKFLOW_STAGES = ["Draft", "Revise", "Polish", "Final"]

# ================== HELPERS ==================
def import_manuscript(text):
    chapters = {}
    current = "Chapter 1"
    chapters[current] = {"text": "", "status": "Draft"}

    for line in text.splitlines():
        if line.strip().lower().startswith("chapter"):
            current = line.strip()
            chapters[current] = {"text": "", "status": "Draft"}
        else:
            chapters[current]["text"] += line + "\n"

    return chapters

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("Projects")

    project_names = list(projects.keys())
    selected = st.selectbox(
        "Select project",
        project_names,
        index=project_names.index(st.session_state.current_project),
    )
    st.session_state.current_project = selected
    project = projects[selected]

    new_project = st.text_input("New project name")
    if st.button("Add Project") and new_project:
        projects[new_project] = {
            "story_bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world_rules": "",
                "characters": []
            },
            "outline": "",
            "chapters": {
                "Chapter 1": {"text": "", "status": "Draft"}
            }
        }
        st.session_state.current_project = new_project

    st.divider()
    st.header("Story Bible")

    sb = project["story_bible"]
    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("Characters")
    cname = st.text_input("Character name")
    cdesc = st.text_area("Character description")
    if st.button("Add Character") and cname:
        sb["characters"].append({"name": cname, "description": cdesc})

    st.divider()
    st.header("Outline")
    project["outline"] = st.text_area("Outline / Beats", project["outline"], height=200)

    st.divider()
    st.header("Import Manuscript")
    uploaded = st.file_uploader("Upload .txt manuscript", type=["txt"])
    if uploaded:
        raw = uploaded.read().decode("utf-8")
        project["chapters"] = import_manuscript(raw)
        st.success("Manuscript imported and split into chapters")

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("Writing")

    filter_stage = st.selectbox("Filter by workflow stage", ["All"] + WORKFLOW_STAGES)

    chapter_names = list(project["chapters"].keys())
    if filter_stage != "All":
        chapter_names = [
            c for c in chapter_names
            if project["chapters"][c]["status"] == filter_stage
        ]

    chapter = st.selectbox("Chapter", chapter_names)

    chapter_data = project["chapters"][chapter]

    chapter_data["status"] = st.selectbox(
        "Workflow status",
        WORKFLOW_STAGES,
        index=WORKFLOW_STAGES.index(chapter_data["status"])
    )

    chapter_data["text"] = st.text_area(
        "Chapter Text",
        chapter_data["text"],
        height=420
    )

    new_chapter = st.text_input("New chapter name")
    if st.button("Add Chapter") and new_chapter:
        project["chapters"][new_chapter] = {
            "text": "",
            "status": "Draft"
        }

with right:
    st.header("Workflow Overview")

    for stage in WORKFLOW_STAGES:
        st.subheader(stage)
        for name, data in project["chapters"].items():
            if data["status"] == stage:
                st.markdown(f"- {name}")

    st.info("AI tools will be added after workflow validation.")
