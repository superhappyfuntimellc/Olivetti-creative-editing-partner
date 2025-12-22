import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🖋️ Olivetti — Writer OS v20.0")

client = OpenAI()

# ================== STYLE DATA ==================
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
            "chapters": ["Chapter 1"],
            "chapter_text": {"Chapter 1": ""},
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
        "Editorial Report": "Provide editorial feedback only."
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
            "chapters": ["Chapter 1"],
            "chapter_text": {"Chapter 1": ""},
            "genre_style": "Lyrical",
            "voice": "Default",
            "tense": "Past",
            "style_sample": "",
            "style_profile": ""
        }
        st.stop()

    st.divider()
    st.header("🎭 Style Controls")
    project["genre_style"] = st.selectbox("Genre", GENRE_STYLES.keys(),
        index=list(GENRE_STYLES.keys()).index(project["genre_style"]))
    project["voice"] = st.selectbox("Voice", VOICE_PRESETS.keys(),
        index=list(VOICE_PRESETS.keys()).index(project["voice"]))
    project["tense"] = st.selectbox("Tense", ["Past","Present"],
        index=["Past","Present"].index(project["tense"]))

    st.divider()
    st.header("🧬 Match My Writing Style")
    project["style_sample"] = st.text_area(
        "Paste your writing",
        project["style_sample"],
        height=150
    )

    if st.button("Analyze Style") and project["style_sample"].strip():
        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0.3,
            input=f"Analyze this author's writing style:\n{project['style_sample']}"
        )
        project["style_profile"] = response.output_text
        st.success("Style profile saved.")

    st.divider()
    st.header("📥 Import Chapter (.txt)")
    upload = st.file_uploader("Upload text", type=["txt"])
    if upload:
        text = upload.read().decode("utf-8")
        new_name = f"Imported {len(project['chapters'])+1}"
        project["chapters"].append(new_name)
        project["chapter_text"][new_name] = text
        st.success(f"{new_name} added.")

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("📖 Chapters")

    chapter = st.selectbox("Chapter", project["chapters"])
    project["chapter_text"][chapter] = st.text_area(
        "Chapter Text",
        project["chapter_text"][chapter],
        height=320
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬆ Move Up"):
            i = project["chapters"].index(chapter)
            if i > 0:
                project["chapters"][i], project["chapters"][i-1] = \
                    project["chapters"][i-1], project["chapters"][i]
                st.stop()
    with col2:
        if st.button("⬇ Move Down"):
            i = project["chapters"].index(chapter)
            if i < len(project["chapters"])-1:
                project["chapters"][i], project["chapters"][i+1] = \
                    project["chapters"][i+1], project["chapters"][i]
                st.stop()

    st.divider()
    st.subheader("🔁 Find & Replace")
    find = st.text_input("Find")
    replace = st.text_input("Replace")
    scope = st.radio("Scope", ["This Chapter", "All Chapters"])

    if st.button("Apply Replace") and find:
        if scope == "This Chapter":
            project["chapter_text"][chapter] = project["chapter_text"][chapter].replace(find, replace)
        else:
            for c in project["chapters"]:
                project["chapter_text"][c] = project["chapter_text"][c].replace(find, replace)
        st.success("Replacement complete.")

    st.divider()
    st.subheader("🔍 Synonym Suggestions")
    word = st.text_input("Word to improve")

    if st.button("Suggest Synonyms") and word:
        context = project["chapter_text"][chapter]
        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0.4,
            input=f"""
Suggest better alternatives for the word "{word}".
Respect author style, genre, and tone.

Context:
{context}
"""
        )
        st.text_area("Suggestions", response.output_text, height=150)

    tool = st.selectbox(
        "AI Tool",
        ["Rewrite","Expand","Describe","Brainstorm","Editorial Report"]
    )
    creativity = st.slider("Creativity", 0.0, 1.0, 0.6)
    run = st.button("Run AI")

with right:
    st.header("🧠 AI Output")

    if run and project["chapter_text"][chapter].strip():
        system_prompt = f"""
You are Olivetti, a professional editor.

Author Style:
{project['style_profile']}

Genre:
{GENRE_STYLES[project['genre_style']]}

Voice:
{VOICE_PRESETS[project['voice']]}

Tense:
{project['tense']}

Canon:
{build_bible(project['bible'])}
"""

        user_prompt = f"""
TASK: {instruction_for(tool)}

TEXT:
{project['chapter_text'][chapter]}
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
        )

        st.text_area("Result", response.output_text, height=420)
