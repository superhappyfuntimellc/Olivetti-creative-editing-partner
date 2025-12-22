import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🖋️ Olivetti — Writer OS v15.0")

client = OpenAI()

# ================== CONSTANTS ==================
GENRE_STYLES = {
    "Comedy": "Witty, playful, sharp timing, humorous observations.",
    "Noir": "Hard-edged, cynical, moody, sparse.",
    "Lyrical": "Poetic, flowing, image-rich, emotional.",
    "Ironic": "Detached, clever, self-aware, understated.",
    "Thriller": "Fast-paced, tense, vivid action, urgency."
}

VOICE_PRESETS = {
    "Default": "Neutral, clear, professional.",
    "Literary": "Elegant prose, interiority, metaphor.",
    "Minimal": "Lean sentences, restraint, implication.",
    "Noir": "Dry voice, blunt imagery, cynicism."
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
            "genre_style": "Literary",
            "voice": "Default",
            "tense": "Past",
            "style_sample": ""
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
                out.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(out)

def instruction_for(tool):
    return {
        "Expand": "Continue naturally. Do not summarize.",
        "Rewrite": "Rewrite with better clarity and flow.",
        "Describe": "Add sensory detail and emotion.",
        "Brainstorm": "Generate ideas or next beats.",
        "Grammar & Style": "Correct grammar and improve style without changing voice."
    }[tool]

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
            "genre_style": "Literary",
            "voice": "Default",
            "tense": "Past",
            "style_sample": ""
        }
        st.stop()

    st.divider()
    st.header("📘 Story Bible")
    sb = project["bible"]
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

    st.divider()
    st.header("🎨 Style Controls")
    project["genre_style"] = st.selectbox(
        "Genre Style", list(GENRE_STYLES.keys()),
        index=list(GENRE_STYLES.keys()).index(project["genre_style"])
    )

    project["voice"] = st.selectbox(
        "Voice Preset", list(VOICE_PRESETS.keys()),
        index=list(VOICE_PRESETS.keys()).index(project["voice"])
    )

    project["tense"] = st.radio(
        "Tense", ["Past", "Present"], horizontal=True,
        index=0 if project["tense"] == "Past" else 1
    )

    st.subheader("✍️ Match My Writing Style")
    project["style_sample"] = st.text_area(
        "Paste your writing sample",
        project["style_sample"],
        height=160
    )
    use_personal_style = st.checkbox("Use my writing style")

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter = st.selectbox("Chapter", list(chapters.keys()))
    chapters[chapter] = st.text_area(
        "Chapter Text",
        chapters[chapter],
        height=350
    )

    tool = st.selectbox(
        "Tool",
        ["Grammar & Style", "Expand", "Rewrite", "Describe", "Brainstorm"]
    )

    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)
    run = st.button("Run")

    st.divider()
    st.subheader("🔁 Synonym Suggestions")
    synonym_text = st.text_input("Word or phrase")
    suggest = st.button("Suggest Synonyms")

with right:
    st.header("🤖 AI Output")

    if run and chapters[chapter].strip():
        system = f"""
You are Olivetti, a professional editor.

Tense: {project['tense']}
Genre Style: {GENRE_STYLES[project['genre_style']]}
Voice Preset: {VOICE_PRESETS[project['voice']]}

Canon:
{build_bible(project['bible'])}
"""

        if use_personal_style and project["style_sample"].strip():
            system += f"""

Match the *writing style only* of this author sample.
Do NOT copy content.

AUTHOR STYLE SAMPLE:
{project['style_sample']}
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": f"{instruction_for(tool)}\n\nTEXT:\n{chapters[chapter]}"
                }
            ],
        )

        st.text_area("Result", response.output_text, height=320)

    if suggest and synonym_text.strip():
        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0.4,
            input=f"Give 10 strong synonym alternatives for: '{synonym_text}'"
        )
        st.text_area("Synonyms", response.output_text, height=200)
