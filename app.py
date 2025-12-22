import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v6.0")

client = OpenAI()

# ================== STATE ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "My First Project": {
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
    st.session_state.active_project = "My First Project"

projects = st.session_state.projects

# ================== STYLE SYSTEM ==================
VOICE_PROFILES = {
    "Default": "",
    "Comedy": "Witty, playful, sharp humor.",
    "Noir": "Hard-boiled, cynical, spare prose.",
    "Lyrical": "Poetic rhythm, metaphor-rich.",
    "Thriller": "Urgent pacing and tension.",
    "Ironic": "Detached, understated wit."
}

GENRE_STYLES = {
    "None": "",
    "Comedy": "Emphasize humor and comic timing.",
    "Noir": "Dark tone, moral ambiguity.",
    "Lyrical": "Focus on beauty of language.",
    "Thriller": "Heighten suspense and danger.",
    "Ironic": "Contrast tone with events."
}

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
        "Rewrite": "Rewrite with better clarity and flow.",
        "Describe": "Add richer sensory detail.",
        "Brainstorm": "Generate creative ideas."
    }[tool]

# ================== SIDEBAR — PROJECTS ==================
with st.sidebar:
    st.header("📁 Projects")

    project_names = list(projects.keys())
    selected = st.selectbox(
        "Active Project",
        project_names,
        index=project_names.index(st.session_state.active_project)
    )

    st.session_state.active_project = selected
    project = projects[selected]

    st.divider()

    new_name = st.text_input("Rename project", value=selected)
    if new_name and new_name != selected:
        projects[new_name] = projects.pop(selected)
        st.session_state.active_project = new_name

    st.divider()

    create_name = st.text_input("New project name")
    if st.button("➕ Create Project") and create_name:
        if create_name not in projects:
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

# ================== MAIN PAGES ==================
tabs = st.tabs(["📘 Story Bible", "🧭 Outline", "✍️ Writing"])

# ---------- STORY BIBLE ----------
with tabs[0]:
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

# ---------- OUTLINE ----------
with tabs[1]:
    project["outline"] = st.text_area(
        "Outline / Beats",
        project["outline"],
        height=400
    )

# ---------- WRITING ----------
with tabs[2]:
    chapters = project["chapters"]

    chapter_name = st.selectbox("Chapter", list(chapters.keys()))

    if st.button("➕ New Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = ""

    chapters[chapter_name] = st.text_area(
        "Chapter Text",
        chapters[chapter_name],
        height=350
    )

    tool = st.selectbox("Tool", ["Expand", "Rewrite", "Describe", "Brainstorm"])
    voice = st.selectbox("Voice", list(VOICE_PROFILES.keys()))
    genre_style = st.selectbox("Genre Style", list(GENRE_STYLES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    if st.button("Run AI") and chapters[chapter_name].strip():
        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "Follow the story bible strictly.\n\n"
            f"{build_story_bible(sb)}"
        )

        if VOICE_PROFILES[voice]:
            system_prompt += f"\n\nVOICE:\n{VOICE_PROFILES[voice]}"
        if GENRE_STYLES[genre_style]:
            system_prompt += f"\n\nGENRE STYLE:\n{GENRE_STYLES[genre_style]}"

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"{instruction_for(tool)}\n\n{chapters[chapter_name]}"
                }
            ],
        )

        st.text_area("🤖 AI Output", response.output_text, height=350)
