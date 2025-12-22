import streamlit as st
from openai import OpenAI
from io import StringIO
import difflib

try:
    from docx import Document
    DOCX_OK = True
except:
    DOCX_OK = False

# ================= CONFIG =================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v12.1 (Chapters Reorderable)")

client = OpenAI()

# ================= STATE ==================
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
            "chapter_summaries": {},
            "voices": {},
            "chapter_order": ["Chapter 1"],
            "chapters": {"Chapter 1": ""}
        }
    }

if "current_project" not in st.session_state:
    st.session_state.current_project = "New Project"

projects = st.session_state.projects
project = projects[st.session_state.current_project]

# ================= VOICES =================
GENRE_VOICES = {
    "Neutral": "",
    "Comedy": "Light, timing-aware, playful phrasing.",
    "Noir": "Hard-boiled, clipped sentences, cynical tone.",
    "Lyrical": "Musical language, metaphor-rich.",
    "Thriller": "Fast pacing, suspense-forward.",
    "Ironic": "Detached, observational, sharp."
}

# ================= HELPERS =================
def extract_text(upload):
    if upload.type == "text/plain":
        return StringIO(upload.getvalue().decode("utf-8")).read()
    if upload.type.endswith("wordprocessingml.document") and DOCX_OK:
        doc = Document(upload)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def build_story_bible(sb):
    out = []
    for k, v in sb.items():
        if not v:
            continue
        if isinstance(v, list):
            out.append("Characters:")
            for c in v:
                out.append(f"- {c['name']}: {c['description']}")
        else:
            out.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(out)

def plagiarism_check(text):
    sents = [s.strip() for s in text.split(".") if len(s.strip()) > 25]
    hits = 0
    for i in range(len(sents)):
        for j in range(i+1, len(sents)):
            if difflib.SequenceMatcher(None, sents[i], sents[j]).ratio() > 0.85:
                hits += 1
    if hits > 6:
        return "HIGH", hits
    if hits > 3:
        return "MEDIUM", hits
    return "LOW", hits

def instruction(tool):
    return {
        "Expand": "Continue the text naturally.",
        "Rewrite": "Rewrite for clarity and quality.",
        "Describe": "Add vivid sensory detail.",
        "Brainstorm": "Generate ideas or beats.",
        "Grammar": "Fix grammar only."
    }[tool]

def move_item(lst, index, direction):
    new = index + direction
    if 0 <= new < len(lst):
        lst[index], lst[new] = lst[new], lst[index]

# ================= SIDEBAR =================
with st.sidebar:
    st.header("📁 Projects")

    names = list(projects.keys())
    selected = st.selectbox(
        "Active Project",
        names,
        index=names.index(st.session_state.current_project)
    )
    st.session_state.current_project = selected
    project = projects[selected]

    new_project = st.text_input("New project name")
    if st.button("➕ Add Project") and new_project:
        projects[new_project] = {
            "story_bible": {
                "title": "", "genre": "", "tone": "",
                "themes": "", "world_rules": "", "characters": []
            },
            "outline": "",
            "chapter_summaries": {},
            "voices": {},
            "chapter_order": ["Chapter 1"],
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

# ================= MAIN ====================
left, right = st.columns(2)

with left:
    st.header("📑 Chapters")

    order = project["chapter_order"]

    for i, name in enumerate(order):
        c1, c2, c3 = st.columns([6,1,1])
        with c1:
            if st.button(name, key=f"select_{name}"):
                st.session_state.current_chapter = name
        with c2:
            if st.button("↑", key=f"up_{name}"):
                move_item(order, i, -1)
        with c3:
            if st.button("↓", key=f"down_{name}"):
                move_item(order, i, 1)

    new_chap = st.text_input("New chapter name")
    if st.button("➕ Add Chapter") and new_chap:
        project["chapters"][new_chap] = ""
        project["chapter_order"].append(new_chap)

    chap = st.session_state.get("current_chapter", order[0])

    st.divider()
    st.header("✍️ Writing")

    text = st.text_area(
        "Chapter Text",
        project["chapters"].get(chap, ""),
        height=300
    )
    project["chapters"][chap] = text

    upload = st.file_uploader("Import TXT / DOCX", type=["txt","docx"])
    if upload:
        imported = extract_text(upload)
        if imported:
            project["chapters"][chap] = imported

with right:
    st.header("🤖 AI Tools")

    tool = st.selectbox(
        "Tool",
        ["Expand","Rewrite","Describe","Brainstorm","Grammar"]
    )
    tense = st.selectbox("Tense", ["Past","Present"])
    genre_style = st.selectbox("Genre Style", list(GENRE_VOICES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    if st.button("Run AI") and text.strip():
        system_prompt = f"""
You are a professional novelist.
Write in {tense} tense.
Genre style: {genre_style}.
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role":"system","content":system_prompt},
                {"role":"user","content":f"{instruction(tool)}\n\n{text}"}
            ]
        )

        output = response.output_text
        st.subheader("AI Output")
        st.text_area("Result", value=output, height=300)

        risk, hits = plagiarism_check(output)
        st.caption(f"Plagiarism signal: {risk} ({hits} repeats)")
