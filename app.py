import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🖋️ Olivetti — Writer OS v17.0")

client = OpenAI()

# ================== STYLES ==================
GENRE_STYLES = {
    "Comedy": "Witty, playful, sharp timing.",
    "Noir": "Hard-edged, cynical, moody.",
    "Lyrical": "Poetic, flowing, emotional.",
    "Ironic": "Detached, clever, understated.",
    "Thriller": "Fast-paced, tense, urgent."
}

VOICE_PRESETS = {
    "Default": "Neutral, clear.",
    "Literary": "Elegant prose, metaphor-rich.",
    "Minimal": "Lean, restrained.",
    "Noir": "Dry, blunt."
}

# ================== DATA MODEL ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "My First Project": {
            "bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world_rules": "",
                "characters": []
            },
            "outline": "",
            "chapters": {"Chapter 1": ""},
            "genre_style": "Lyrical",
            "voice": "Default",
            "tense": "Past"
        }
    }

projects = st.session_state.projects

# ================== HELPERS ==================
def build_bible(sb):
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
        "Grammar & Style": "Correct grammar and polish style.",
        "Expand": "Continue naturally without summarizing.",
        "Rewrite": "Rewrite with better flow and clarity.",
        "Describe": "Add sensory detail and emotion.",
        "Brainstorm": "Generate ideas or next beats."
    }[tool]

def export_project_text(project):
    lines = []
    lines.append(project["bible"].get("title", "").upper())
    lines.append("\n")
    for name, text in project["chapters"].items():
        lines.append(f"\n\n### {name}\n\n{text}")
    return "\n".join(lines)

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_names = list(projects.keys())
    current = st.selectbox("Project", project_names)
    project = projects[current]

    rename = st.text_input("Rename project", current)
    if rename and rename != current:
        projects[rename] = projects.pop(current)
        st.stop()

    if st.button("➕ New Project"):
        projects[f"Project {len(projects)+1}"] = {
            "bible": {
                "title": "", "genre": "", "tone": "",
                "themes": "", "world_rules": "", "characters": []
            },
            "outline": "",
            "chapters": {"Chapter 1": ""},
            "genre_style": "Lyrical",
            "voice": "Default",
            "tense": "Past"
        }
        st.stop()

    st.divider()
    st.header("📥 Import")

    upload = st.file_uploader("Import TXT", type=["txt"])
    import_mode = st.radio("Import as", ["New Project", "New Chapter"])

    if upload:
        content = upload.read().decode("utf-8")
        if st.button("Import"):
            if import_mode == "New Project":
                projects[upload.name] = {
                    "bible": {
                        "title": upload.name.replace(".txt",""),
                        "genre": "", "tone": "",
                        "themes": "", "world_rules": "", "characters": []
                    },
                    "outline": "",
                    "chapters": {"Chapter 1": content},
                    "genre_style": "Lyrical",
                    "voice": "Default",
                    "tense": "Past"
                }
            else:
                project["chapters"][upload.name] = content
            st.stop()

    st.divider()
    st.header("📘 Story Bible")
    sb = project["bible"]
    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules", sb["world_rules"])

    st.divider()
    st.header("📤 Export")
    export_text = export_project_text(project)
    st.download_button(
        "Download Project (.txt)",
        export_text,
        file_name=f"{current}.txt"
    )

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("📖 Chapters")

    chapter_names = list(project["chapters"].keys())
    chapter = st.selectbox("Chapter", chapter_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("⬆ Move Up"):
            i = chapter_names.index(chapter)
            if i > 0:
                chapter_names[i-1], chapter_names[i] = chapter_names[i], chapter_names[i-1]
                project["chapters"] = {k: project["chapters"][k] for k in chapter_names}
                st.stop()
    with col2:
        if st.button("⬇ Move Down"):
            i = chapter_names.index(chapter)
            if i < len(chapter_names)-1:
                chapter_names[i+1], chapter_names[i] = chapter_names[i], chapter_names[i+1]
                project["chapters"] = {k: project["chapters"][k] for k in chapter_names}
                st.stop()
    with col3:
        if st.button("❌ Delete"):
            project["chapters"].pop(chapter)
            st.stop()

    project["chapters"][chapter] = st.text_area(
        "Chapter Text",
        project["chapters"][chapter],
        height=380
    )

    tool = st.selectbox(
        "Tool",
        ["Grammar & Style", "Expand", "Rewrite", "Describe", "Brainstorm"]
    )
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)
    run = st.button("Run AI")

with right:
    st.header("🤖 AI Output")

    if run and project["chapters"][chapter].strip():
        system = f"""
You are Olivetti, a professional editor.

Tense: {project['tense']}
Genre: {GENRE_STYLES[project['genre_style']]}
Voice: {VOICE_PRESETS[project['voice']]}

Canon:
{build_bible(project['bible'])}
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"{instruction_for(tool)}\n\nTEXT:\n{project['chapters'][chapter]}"
                }
            ],
        )

        st.text_area("Result", response.output_text, height=420)
