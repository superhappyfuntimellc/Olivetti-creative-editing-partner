import streamlit as st
from openai import OpenAI
from datetime import datetime

# ================== SETUP ==================
client = OpenAI()
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — Story Bible Edition")

# ================== DATA MODEL ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "New Novel": {
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
        if v:
            if isinstance(v, list):
                out.append("Characters:")
                for c in v:
                    out.append(f"- {c['name']}: {c['description']}")
            else:
                out.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(out)

def instruction_for(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite with better clarity and flow.",
        "Describe": "Add richer sensory detail and emotion.",
        "Brainstorm": "Generate ideas, plot beats, or options."
    }[tool]

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📚 Projects")
    project_name = st.selectbox("Project", list(projects.keys()))
    project = projects[project_name]

    if st.button("➕ New Project"):
        projects[f"Novel {len(projects)+1}"] = {
            "story_bible": {
                "title": "", "genre": "", "tone": "",
                "themes": "", "world_rules": "", "characters": []
            },
            "outline": "",
            "chapters": {"Chapter 1": {"text": "", "locked": False}}
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

    st.subheader("Characters")
    cname = st.text_input("Name")
    cdesc = st.text_area("Description")
    if st.button("Add Character") and cname:
        sb["characters"].append({"name": cname, "description": cdesc})

    st.divider()
    st.header("🧭 Outline / Beats")
    project["outline"] = st.text_area("Outline", project["outline"], height=200)

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name =
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))
    chapter = chapters[chapter_name]

    chapter["locked"] = st.checkbox("🔒 Lock this chapter", value=chapter["locked"])

    chapter["text"] = st.text_area(
        "Chapter Text",
        chapter["text"],
        height=300,
        disabled=chapter["locked"]
    )

    tool = st.selectbox("Tool", ["Expand", "Rewrite", "Describe", "Brainstorm"])
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)
    run = st.button("Run")

# ================== OUTPUT ==================
with right:
    st.header("🤖 AI Output")

    if run and chapter["text"].strip():
        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "You MUST follow the story bible exactly.\n"
            "Do NOT modify locked text.\n\n"
            f"STORY BIBLE:\n{build_story_bible(project['story_bible'])}\n\n"
            f"OUTLINE:\n{project['outline']}"
        )

        user_prompt = (
            f"{instruction_for(tool)}\n\n"
            f"TEXT:\n{chapter['text']}"
        )

        with st.spinner("Writing…"):
            try:
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    temperature=creativity,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                )

                st.text_area(
                    "Result",
                    response.output_text,
                    height=400
                )

            except Exception:
                st.error(
                    "⚠️ Temporary connection issue.\n\n"
                    "Please wait a moment and click **Run** again."
                )

