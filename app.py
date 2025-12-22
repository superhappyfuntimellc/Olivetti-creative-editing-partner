import streamlit as st

# ================== PAGE SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v7.0 (Voices & Tense)")

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
            "settings": {
                "voice": "Neutral",
                "tense": "Past"
            },
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

    # Rename project
    rename = st.text_input("Rename project", value=active)
    if rename and rename != active and rename not in projects:
        projects[rename] = projects.pop(active)
        st.session_state.active_project = rename
        st.rerun()

    # Create project
    st.divider()
    new_project = st.text_input("New project name")
    if st.button("➕ Create Project"):
        if new_project and new_project not in projects:
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
                "settings": {
                    "voice": "Neutral",
                    "tense": "Past"
                },
                "chapters": {"Chapter 1": ""}
            }
            st.session_state.active_project = new_project
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

    # Chapter system
    chapters = project["chapters"]
    chapter_names = list(chapters.keys())
    chapter = st.selectbox("Chapter", chapter_names)

    chapters[chapter] = st.text_area(
        "Chapter Text",
        chapters[chapter],
        height=420
    )

    if st.button("➕ Add Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = ""
        st.rerun()

with right:
    st.header("🎭 Style Controls")

    settings = project["settings"]

    settings["voice"] = st.selectbox(
        "Voice / Style",
        ["Neutral", "Comedy", "Noir", "Lyrical", "Ironic", "Thriller"],
        index=["Neutral", "Comedy", "Noir", "Lyrical", "Ironic", "Thriller"].index(settings["voice"])
    )

    settings["tense"] = st.radio(
        "Narrative Tense",
        ["Past", "Present", "Future"],
        index=["Past", "Present", "Future"].index(settings["tense"])
    )

    st.divider()
    st.header("🤖 AI Output")
    st.info(
        f"""
**v7.0 ready**

Voice: **{settings['voice']}**  
Tense: **{settings['tense']}**

AI generation, spellcheck, grammar, and exports come next.
"""
    )
