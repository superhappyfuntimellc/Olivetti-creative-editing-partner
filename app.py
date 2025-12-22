import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
client = OpenAI()

st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v2.1 (Projects, Chapters, Autosave)")

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
    if sb["title"]:
        out.append(f"Title: {sb['title']}")
    if sb["genre"]:
        out.append(f"Genre: {sb['genre']}")
    if sb["tone"]:
        out.append(f"Tone: {sb['tone']}")
    if sb["themes"]:
        out.append(f"Themes: {sb['themes']}")
    if sb["world_rules"]:
        out.append("World Rules / Canon:")
        out.append(sb["world_rules"])
    if sb["characters"]:
        out.append("Characters:")
        for c in sb["characters"]:
            out.append(f"- {c['name']}: {c['description']}")
    return "\n".join(out)

def instruction_for(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite with improved clarity and flow.",
        "Describe": "Rewrite with richer sensory detail and emotion.",
        "Brainstorm": "Generate ideas, plot beats, or options."
    }[tool]

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_name = st.selectbox("Project", list(projects.keys()))

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
            "outline": "",
            "chapters": {
                "Chapter 1": {
                    "text": "",
                    "locked": False
                }
            }
        }
        st.rerun()

    project = projects[project_name]
    sb = project["story_bible"]

    st.divider()
    st.header("📘 Story Bible")

    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("🧍 Characters")
    cname = st.text_input("Character name")
    cdesc = st.text_area("Character description")

    if st.button("Add / Update Character") and cname.strip():
        sb["characters"] = [c for c in sb["characters"] if c["name"] != cname]
        sb["characters"].append({"name": cname, "description": cdesc})
        st.rerun()

    for c in sb["characters"]:
        st.markdown(f"**{c['name']}** — {c['description']}")

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
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))
    chapter = chapters[chapter_name]

    if st.button("➕ New Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = {
            "text": "",
            "locked": False
        }
        st.rerun()

    new_name = st.text_input("Rename chapter", chapter_name)
    if new_name and new_name != chapter_name:
        chapters[new_name] = chapters.pop(chapter_name)
        st.rerun()

    chapter["locked"] = st.checkbox("🔒 Lock chapter", chapter["locked"])

    chapter["text"] = st.text_area(
        "Chapter Text",
        chapter["text"],
        height=350,
        disabled=chapter["locked"]
    )

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm"]
    )

    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run = st.button("Run AI")

with right:
    st.header("🤖 AI Output")

    if run and chapter["text"].strip() and not chapter["locked"]:
        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "You MUST follow the story bible exactly.\n\n"
            f"STORY BIBLE:\n{build_story_bible(sb)}"
        )

        with st.spinner("Writing…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=creativity,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"{instruction_for(tool)}\n\nTEXT:\n{chapter['text']}"
                    }
                ],
            )

        st.text_area("Result", value=response.output_text, height=400)
