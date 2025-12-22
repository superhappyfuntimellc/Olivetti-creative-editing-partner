import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v3.0")

client = OpenAI()

# ================== STATE ==================
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
            "chapters": {
                "Chapter 1": ""
            }
        }
    }

projects = st.session_state.projects

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")
    project_name = st.selectbox("Project", list(projects.keys()))
    project = projects[project_name]

    if st.button("➕ New Project"):
        projects[f"Project {len(projects)+1}"] = {
            "story_bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world_rules": "",
                "characters": []
            },
            "chapters": {
                "Chapter 1": ""
            }
        }

    st.divider()
    st.header("📘 Story Bible")
    sb = project["story_bible"]

    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("Characters")
    name = st.text_input("Character name")
    desc = st.text_area("Character description")

    if st.button("Add Character") and name:
        sb["characters"].append({"name": name, "description": desc})

    for c in sb["characters"]:
        st.markdown(f"• **{c['name']}** — {c['description']}")

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))

    if st.button("➕ New Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = ""

    chapters[chapter_name] = st.text_area(
        "Chapter Text",
        chapters[chapter_name],
        height=400
    )

with right:
    st.header("🤖 AI Output")
    st.info("v3.0 foundation locked. No AI tools yet.")
