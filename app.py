import streamlit as st
from openai import OpenAI
from docx import Document
from io import BytesIO

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🖋️ Olivetti — Writer OS v21.0")

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

def export_docx(chapters, texts):
    doc = Document()
    for c in chapters:
        doc.add_heading(c, level=1)
        doc.add_paragraph(texts[c])
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    current = st.selectbox("Project", list(projects.keys()))
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
    project["style_sample"] = st.text_area("Paste your writing", project["style_sample"], height=120)

    if st.button("Analyze Style") and project["style_sample"].strip():
        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0.3,
            input=f"Analyze this author's writing style:\n{project['style_sample']}"
        )
        project["style_profile"] = response.output_text
        st.success("Style profile saved.")

    st.divider()
    st.header("📥 Import")
    upload = st.file_uploader("Import TXT or DOCX", type=["txt","docx"])
    if upload:
        if upload.name.endswith(".txt"):
            text = upload.read().decode("utf-8")
        else:
            doc = Document(upload)
            text = "\n".join(p.text for p in doc.paragraphs)
        name = f"Imported {len(project['chapters'])+1}"
        project["chapters"].append(name)
        project["chapter_text"][name] = text
        st.success(f"{name} added.")

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("📖 Chapters")

    chapter = st.selectbox("Chapter", project["chapters"])
    project["chapter_text"][chapter] = st.text_area(
        "Chapter Text",
        project["chapter_text"][chapter],
        height=300
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬆ Move Up"):
            i = project["chapters"].index(chapter)
            if i > 0:
                project["chapters"][i], project["chapters"][i-1] = project["chapters"][i-1], project["chapters"][i]
                st.stop()
    with col2:
        if st.button("⬇ Move Down"):
            i = project["chapters"].index(chapter)
            if i < len(project["chapters"])-1:
                project["chapters"][i], project["chapters"][i+1] = project["chapters"][i+1], project["chapters"][i]
                st.stop()

    st.divider()
    st.subheader("🧭 Outline → Chapters")
    project["outline"] = st.text_area("Outline / Beats", project["outline"], height=150)

    if st.button("Generate Chapters from Outline") and project["outline"].strip():
        beats = [b.strip() for b in project["outline"].split("\n") if b.strip()]
        project["chapters"] = []
        project["chapter_text"] = {}
        for i, b in enumerate(beats, 1):
            name = f"Chapter {i}"
            project["chapters"].append(name)
            project["chapter_text"][name] = f"{b}\n\n[Draft content here]"
        st.success("Chapters generated.")

    st.divider()
    st.subheader("🔍 Similarity Scan")
    if st.button("Run Scan"):
        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            input=f"Analyze this text for clichés, overused phrasing, or generic constructions:\n{project['chapter_text'][chapter]}"
        )
        st.text_area("Editorial Notes", response.output_text, height=150)

with right:
    st.header("🧠 AI Output")

    tool = st.selectbox("AI Tool", ["Rewrite","Expand","Describe","Brainstorm","Editorial Report"])
    creativity = st.slider("Creativity", 0.0, 1.0, 0.6)

    if st.button("Run AI"):
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

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{instruction_for(tool)}\n\n{project['chapter_text'][chapter]}"}
            ],
        )

        st.text_area("Result", response.output_text, height=420)

    st.divider()
    st.subheader("📦 Export")
    docx_file = export_docx(project["chapters"], project["chapter_text"])
    st.download_button("Download DOCX", docx_file, "project.docx")
