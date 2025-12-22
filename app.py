import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v4.0 (Voices & AI Tools)")

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
                out.append(f"{k.title()}: {v}")
    return "\n".join(out)

def instruction_for(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite the text with improved clarity and flow.",
        "Describe": "Add richer sensory detail and emotion.",
        "Brainstorm": "Generate creative ideas or next plot beats."
    }[tool]

VOICE_PROFILES = {
    "Default": "",
    "Comedy": "Witty, playful, humorous tone with timing and surprise.",
    "Noir": "Hard-boiled, cynical, sharp imagery, restrained emotion.",
    "Lyrical": "Musical language, metaphor, flowing sentences.",
    "Thriller": "Tight pacing, tension, urgency, vivid action.",
    "Ironic": "Detached, clever, subtle humor, knowing voice."
}

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

    tool = st.selectbox("Tool", ["Expand", "Rewrite", "Describe", "Brainstorm"])
    voice = st.selectbox("Voice", list(VOICE_PROFILES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run = st.button("Run AI")

with right:
    st.header("🤖 AI Output")

    if run and chapters[chapter_name].strip():
        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "You must follow the story bible exactly.\n\n"
            f"STORY BIBLE:\n{build_story_bible(sb)}"
        )

        if VOICE_PROFILES[voice]:
            system_prompt += f"\n\nSTYLE:\n{VOICE_PROFILES[voice]}"

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"{instruction_for(tool)}\n\nTEXT:\n{chapters[chapter_name]}"
                }
            ],
        )

        st.text_area("Result", response.output_text, height=400)
