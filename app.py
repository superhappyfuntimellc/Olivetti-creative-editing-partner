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
st.title("📝 Pro Writer Suite — v10.2")

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
            "chapters": {"Chapter 1": ""}
        }
    }

if "current_project" not in st.session_state:
    st.session_state.current_project = "New Project"

projects = st.session_state.projects
project = projects[st.session_state.current_project]

# ================= HELPERS =================
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

def instruction(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite for clarity, flow, and quality.",
        "Describe": "Add vivid sensory detail and emotion.",
        "Brainstorm": "Generate ideas, beats, or directions.",
        "Grammar": "Fix grammar, spelling, and punctuation only."
    }[tool]

def extract_text(upload):
    if upload.type == "text/plain":
        return StringIO(upload.getvalue().decode("utf-8")).read()
    if upload.type.endswith("wordprocessingml.document") and DOCX_OK:
        doc = Document(upload)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

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

# ================= SIDEBAR =================
with st.sidebar:
    st.header("📁 Projects")

    names = list(projects.keys())
    selected = st.selectbox(
        "Select Project",
        names,
        index=names.index(st.session_state.current_project)
    )
    st.session_state.current_project = selected
    project = projects[selected]

    new_name = st.text_input("New project name")
    if st.button("➕ Add Project") and new_name:
        projects[new_name] = {
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
        st.session_state.current_project = new_name

    st.divider()
    st.header("📘 Story Bible")

    sb = project["story_bible"]
    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("🧍 Characters")
    cname = st.text_input("Character name")
    cdesc = st.text_area("Character description")
    if st.button("Add Character") and cname:
        sb["characters"].append({"name": cname, "description": cdesc})

# ================= MAIN ====================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chap_name = st.selectbox("Chapter", list(chapters.keys()))

    new_chap = st.text_input("New chapter name")
    if st.button("Add Chapter") and new_chap:
        chapters[new_chap] = ""
        chap_name = new_chap

    text = st.text_area(
        "Chapter Text",
        value=chapters[chap_name],
        height=300
    )
    chapters[chap_name] = text

    st.subheader("📥 Import Document")
    upload = st.file_uploader("Upload TXT or DOCX", type=["txt", "docx"])
    if upload:
        imported = extract_text(upload)
        if imported:
            chapters[chap_name] = imported
            st.success("Imported successfully.")

    st.subheader("🔍 Find & Replace")
    f = st.text_input("Find")
    r = st.text_input("Replace with")
    if st.button("Replace All") and f:
        chapters[chap_name] = chapters[chap_name].replace(f, r)

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
    st.header("🧭 Outline")
    project["outline"] = st.text_area(
        "Outline / Beats (autosaved)",
        project["outline"],
        height=200
    )

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
                {"role": "user", "content": f"{instruction(tool)}\n\n{text}"}
            ],
        )

        output = response.output_text

        st.subheader("🤖 AI Output")
        st.text_area("Result", value=output, height=300)

        risk, hits = plagiarism_check(output)
        st.subheader("🕵️ Plagiarism Signal")
        st.write(f"Risk: **{risk}** | Repeated segments: {hits}")
