import streamlit as st

# ================== PAGE SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v6.2 (Stable Foundation)")

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
                "Chapter 1": ""
            }
        }
    }

if "active_project" not in st.session_state:
    st.session_state.active_project = "New Project"

projects = st.session_state.projects

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_names = list(projects.keys())
    active = st.selectbox(
        "Active Project",
        project_names,
        index=project_names.index(st.session_state.active_project)
    )

    st.session_state.active_project = active
    project = projects[active]

    # --- Rename project ---
    new_name = st.text_input("Rename project", value=active)
    if new_name and new_name != active and new_name not in projects:
        projects[new_name] = projects.pop(active)
        st.session_state.active_project = new_name
        st.rerun()

    # --- Create project ---
    st.divider()
    create_name = st.text_input("New project name")
    if st.button("➕ Create Project"):
        if create_name and create_name not in projects:
            projects[create_name] = {
                "story_bible": {
                    "title": "",
                    "genre": "",
                    "tone": "",
                    "themes": "",
                    "world_rules": "",
                    "characters": []
                },
                "outline": "",
                "chapters": {"Chapter 1": ""}
            }
            st.session_state.active_project = create_name
            st.rerun()

    # ================= STORY BIBLE =================
    st.divider()
    st.header("📘 Story Bible")
    sb = project["story_bible"]

    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    # ================= CHARACTERS =================
    st.subheader("🧍 Characters")

    cname = st.text_input("Character name")
    cdesc = st.text_area("Character description")

    if st.button("Add / Update Character"):
        if cname:
            sb["characters"] = [c for c in sb["characters"] if c["name"] != cname]
            sb["characters"].append({"name": cname, "description": cdesc})
            st.rerun()

    for c in sb["characters"]:
        st.markdown(f"**{c['name']}** — {c['description']}")

    # ================= OUTLINE =================
    st.divider()
    st.header("🧭 Outline")
    project["outline"] = st.text_area(
        "Outline / Beats",
        project["outline"],
        height=200
    )

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_names = list(chapters.keys())

    chapter = st.selectbox("Chapter", chapter_names)
    chapters[chapter] = st.text_area(
        "Chapter Text",
        chapters[chapter],
        height=400
    )

    if st.button("➕ Add Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = ""
        st.rerun()

with right:
    st.header("🤖 AI Output")
    st.info("v6.2 foundation locked.\n\nAI, voices, tense, styles coming next.")
