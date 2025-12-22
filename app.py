import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🖋️ Olivetti — Writer OS v19.0")

client = OpenAI()

# ================== STYLES ==================
GENRE_STYLES = {
    "Comedy": "Witty, playful, timing-focused.",
    "Noir": "Hard-edged, cynical, moody.",
    "Lyrical": "Poetic, flowing, image-rich.",
    "Ironic": "Detached, clever, understated.",
    "Thriller": "Fast-paced, tense, urgent."
}

VOICE_PRESETS = {
    "Default": "Neutral, clear.",
    "Literary": "Elegant, metaphor-rich.",
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
            "tense": "Past",
            "style_sample": "",
            "style_profile": ""
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
        "Rewrite": "Rewrite with better flow and clarity.",
        "Expand": "Continue naturally without summarizing.",
        "Describe": "Add sensory detail and emotion.",
        "Brainstorm": "Generate ideas or next beats.",
        "Editorial Report": "Do NOT rewrite. Provide editorial feedback only.",
        "Style Analysis": "Analyze the author's writing style only."
    }[tool]

def export_project_text(project):
    lines = []
    lines.append(project["bible"].get("title", "").upper())
    for name, text in project["chapters"].items():
        lines.append(f"\n\n### {name}\n\n{text}")
    return "\n".join(lines)

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    names = list(projects.keys())
    current = st.selectbox("Project", names)
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
            "tense": "Past",
            "style_sample": "",
            "style_profile": ""
        }
        st.stop()

    st.divider()
    st.header("🎭 Style Controls")
    project["genre_style"] = st.selectbox(
        "Genre Style", list(GENRE_STYLES.keys()),
        index=list(GENRE_STYLES.keys()).index(project["genre_style"])
    )
    project["voice"] = st.selectbox(
        "Voice Preset", list(VOICE_PRESETS.keys()),
        index=list(VOICE_PRESETS.keys()).index(project["voice"])
    )
    project["tense"] = st.selectbox(
        "Tense", ["Past", "Present"],
        index=["Past","Present"].index(project["tense"])
    )

    st.divider()
    st.header("🧬 Match My Writing Style")
    project["style_sample"] = st.text_area(
        "Paste a sample of YOUR writing",
        project["style_sample"],
        height=200
    )

    if st.button("Analyze My Style") and project["style_sample"].strip():
        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0.3,
            input=f"""
Analyze the author's writing style.
Describe sentence length, rhythm, tone, figurative density,
dialogue usage, and narrative distance.
Return a concise style profile.

TEXT:
{project['style_sample']}
"""
        )
        project["style_profile"] = response.output_text
        st.success("Style profile saved to project.")

    if project["style_profile"]:
        st.caption("Saved Style Profile:")
        st.text(project["style_profile"])

    st.divider()
    st.header("📤 Export")
    st.download_button(
        "Download Project (.txt)",
        export_project_text(project),
        file_name=f"{current}.txt"
    )

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("📖 Chapters")
    chapter_names = list(project["chapters"].keys())
    chapter = st.selectbox("Chapter", chapter_names)

    project["chapters"][chapter] = st.text_area(
        "Chapter Text",
        project["chapters"][chapter],
        height=380
    )

    tool = st.selectbox(
        "Tool",
        ["Rewrite", "Expand", "Describe", "Brainstorm", "Editorial Report"]
    )
    creativity = st.slider("Creativity", 0.0, 1.0, 0.6)
    run = st.button("Run AI")

with right:
    st.header("🧠 AI & Editorial Output")

    if run and project["chapters"][chapter].strip():
        system_prompt = f"""
You are Olivetti, a professional literary editor.

Primary rule:
Match the author's unique writing style as closely as possible.

Author Style Profile:
{project['style_profile']}

Genre Style:
{GENRE_STYLES[project['genre_style']]}

Voice Preset:
{VOICE_PRESETS[project['voice']]}

Tense:
{project['tense']}

Canon:
{build_bible(project['bible'])}
"""

        user_prompt = f"""
TASK: {instruction_for(tool)}

If TASK is Editorial Report:
- Do NOT rewrite text
- Provide bullet-point feedback under:
  • Style Fidelity
  • Repetition & Echoes
  • POV & Tense Consistency
  • Plagiarism / Familiarity Risk
  • Craft Notes

TEXT:
{project['chapters'][chapter]}
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )

        st.text_area("Result", response.output_text, height=440)
