import streamlit as st
from openai import OpenAI
import difflib

# ================== CONFIG ==================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v10.0")

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
            "chapters": {"Chapter 1": ""},
        }
    }

if "current_project" not in st.session_state:
    st.session_state.current_project = "New Project"

# ================== HELPERS ==================
def build_story_bible(sb):
    parts = []
    for k, v in sb.items():
        if v:
            if isinstance(v, list):
                parts.append("Characters:")
                for c in v:
                    parts.append(f"- {c['name']}: {c['description']}")
            else:
                parts.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(parts)

def plagiarism_check(text):
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
    matches = 0
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            ratio = difflib.SequenceMatcher(None, sentences[i], sentences[j]).ratio()
            if ratio > 0.85:
                matches += 1
    risk = "LOW"
    if matches > 3:
        risk = "MEDIUM"
    if matches > 7:
        risk = "HIGH"
    return risk, matches

def instruction(tool):
    return {
        "Expand": "Continue the text naturally without summarizing.",
        "Rewrite": "Rewrite for clarity, flow, and quality.",
        "Describe": "Add sensory detail and emotional depth.",
        "Brainstorm": "Generate ideas, metaphors, or next plot beats.",
        "Grammar": "Fix grammar, spelling, and punctuation only."
    }[tool]

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    projects = st.session_state.projects
    project_names = list(projects.keys())

    selected = st.selectbox(
        "Select Project",
        project_names,
        index=project_names.index(st.session_state.current_project)
    )
    st.session_state.current_project = selected
    project = projects[selected]

    new_project = st.text_input("New project name")
    if st.button("➕ Add Project") and new_project:
        projects[new_project] = {
            "story_bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world_rules": "",
                "characters": []
            },
            "chapters": {"Chapter 1": ""}
        }
        st.session_state.current_project = new_project

    st.divider()
    st.header("📘 Story Bible")
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

# ================== MAIN ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))

    new_chapter = st.text_input("New chapter name")
    if st.button("Add Chapter") and new_chapter:
        chapters[new_chapter] = ""
        chapter_name = new_chapter

    text = st.text_area(
        "Chapter Text",
        value=chapters[chapter_name],
        height=350
    )
    chapters[chapter_name] = text

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm", "Grammar"]
    )

    tense = st.selectbox("Tense", ["Past", "Present"])

    style = st.selectbox(
        "Genre Style",
        ["Neutral", "Comedy", "Noir", "Lyrical", "Thriller", "Ironic"]
    )

    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)
    run = st.button("Run AI")

with right:
    st.header("🤖 AI Output")

    if run and text.strip():
        bible = build_story_bible(project["story_bible"])

        system_prompt = f"""
You are a professional novelist.
Write in {tense} tense.
Style: {style}.
Follow the story bible exactly.

STORY BIBLE:
{bible}
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"{instruction(tool)}\n\nTEXT:\n{text}"
                }
            ],
        )

        output = response.output_text
        st.text_area("Result", value=output, height=350)

        st.divider()
        st.subheader("🕵️ Plagiarism Check")
        risk, matches = plagiarism_check(output)
        st.write(f"**Risk Level:** {risk}")
        st.write(f"Repeated sentence matches: {matches}")
