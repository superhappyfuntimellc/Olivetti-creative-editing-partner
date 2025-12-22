import streamlit as st
from openai import OpenAI
import json

# ================== SETUP ==================
client = OpenAI()
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v2.1 (Canon, Save & Lock)")

# ================== DATA MODEL ==================
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
                    "locked": False
                }
            }
        }
    }

projects = st.session_state.projects

# ================== HELPERS ==================
def build_story_bible(sb):
    out = []
    for k, v in sb.items():
        if not v:
            continue
        if isinstance(v, list):
            out.append("Characters:")
            for c in v:
                out.append(f"- {c['name']}: {c['description']}")
        else:
            out.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(out)

def build_locked_chapters(chapters):
    out = []
    for name, ch in chapters.items():
        if ch["locked"] and ch["text"].strip():
            out.append(f"{name} (LOCKED):\n{ch['text']}")
    return "\n\n".join(out)

def instruction_for(tool):
    return {
        "Expand": "Continue the text naturally. Do NOT modify locked canon.",
        "Rewrite": "Rewrite the text for clarity. Do NOT contradict locked canon.",
        "Describe": "Add sensory detail without contradicting canon.",
        "Brainstorm": "Generate ideas that respect locked canon."
    }[tool]

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_name = st.radio(
        "Projects",
        list(projects.keys()),
        label_visibility="collapsed"
    )
    project = projects[project_name]

    if st.button("➕ New Project"):
        projects[f"Project {len(projects)+1}"] = {
            "story_bible": {
                "title": "", "genre": "", "tone": "",
                "themes": "", "world_rules": "", "characters": []
            },
            "outline": "",
            "chapters": {
                "Chapter 1": {"text": "", "locked": False}
            }
        }
        st.experimental_rerun()

    st.divider()
    st.header("📘 Story Bible")
    sb = project["story_bible"]

    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("🧍 Characters")
    cname = st.text_input("Character name")
    cdesc = st.text_area("Character description")

    if st.button("Add / Update Character") and cname:
        sb["characters"] = [c for c in sb["characters"] if c["name"] != cname]
        sb["characters"].append({"name": cname, "description": cdesc})

    for c in sb["characters"]:
        st.markdown(f"**{c['name']}** — {c['description']}")

    st.divider()
    st.header("🧭 Outline")
    project["outline"] = st.text_area(
        "Outline / Beats",
        project["outline"],
        height=200
    )

    st.divider()
    st.header("💾 Save / Load")

    export_data = json.dumps(project, indent=2)
    st.download_button(
        "⬇️ Export Project",
        export_data,
        file_name=f"{project_name}.json"
    )

    uploaded = st.file_uploader("⬆️ Import Project", type="json")
    if uploaded:
        projects[project_name] = json.load(uploaded)
        st.experimental_rerun()

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))
    chapter = chapters[chapter_name]

    chapter["text"] = st.text_area(
        "Chapter Text",
        chapter["text"],
        he
