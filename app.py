import streamlit as st
from openai import OpenAI
from datetime import datetime
from docx import Document

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v7.0")

client = OpenAI()

# ================== STATE INIT ==================
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
            "timeline": "",
            "chapters": {
                "Chapter 1": {
                    "text": "",
                    "locked": False,
                    "versions": []
                }
            }
        }
    }

projects = st.session_state.projects

# ================== VOICES ==================
VOICE_PROFILES = {
    "Default": "",
    "Literary": "Long sentences, interiority, metaphor, controlled pacing.",
    "Minimal": "Short sentences, restraint, subtext.",
    "Noir": "Hard edges, cynicism, concrete imagery.",
    "Romantic": "Emotional intimacy, sensory focus.",
    "Epic": "Elevated diction, mythic scale."
}

# ================== HELPERS ==================
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

def instruction_for(tool):
    return {
        "Expand": "Continue naturally. Do not summarize.",
        "Rewrite": "Rewrite for clarity, flow, and style.",
        "Describe": "Add vivid sensory detail.",
        "Brainstorm": "Generate plot ideas or options.",
        "Proofread": "Fix grammar, spelling, and punctuation only.",
        "Diagnostics": "Analyze pacing, POV, tension, continuity. Bullet points."
    }[tool]

def split_scenes(text):
    return [s.strip() for s in text.split("\n\n") if s.strip()]

def export_docx(title, text):
    doc = Document()
    doc.add_heading(title, 1)
    for p in text.split("\n\n"):
        doc.add_paragraph(p)
    return doc

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")
    project_name = st.selectbox("Project", list(projects.keys()))
    project = projects[project_name]

    if st.button("➕ New Project"):
        projects[f"Project {len(projects)+1}"] = {
            "story_bible": {
                "title": "", "genre": "", "tone": "",
                "themes": "", "world_rules": "", "characters": []
            },
            "outline": "",
            "timeline": "",
            "chapters": {"Chapter 1": {"text": "", "locked": False, "versions": []}}
        }

    st.divider()
    st.header("📘 Story Bible")
    sb = project["story_bible"]
    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("🧍 Characters")
    cname = st.text_input("Character Name")
    cdesc = st.text_area("Character Description")
    if st.button("Add / Update Character") and cname:
        sb["characters"] = [c for c in sb["characters"] if c["name"] != cname]
        sb["characters"].append({"name": cname, "description": cdesc})

    st.divider()
    project["outline"] = st.text_area("🧭 Outline", project["outline"], height=120)
    project["timeline"] = st.text_area("⏱ Timeline", project["timeline"], height=120)

# ================== MAIN ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))
    chapter = chapters[chapter_name]

    if st.button("➕ New Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = {"text": "", "locked": False, "versions": []}

    chapter["locked"] = st.checkbox("🔒 Lock Chapter (Canon)", chapter["locked"])

    chapter_text = st.text_area(
        "Chapter Text",
        chapter["text"],
        height=320,
        disabled=chapter["locked"]
    )

    if not chapter["locked"]:
        chapter["text"] = chapter_text

    pov = st.selectbox("POV Lock", ["None"] + [c["name"] for c in sb["characters"]])
    focus = st.selectbox("Character Focus", ["None"] + [c["name"] for c in sb["characters"]])

    tense = st.selectbox("Narrative Tense", ["Keep Original", "Past", "Present", "Future"])
    tool = st.selectbox("Tool", list(instruction_for.__annotations__) if False else
        ["Expand", "Rewrite", "Describe", "Brainstorm", "Proofread", "Diagnostics"]
    )

    voice = st.selectbox("Voice", list(VOICE_PROFILES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)
    run = st.button("Run")

with right:
    st.header("🤖 AI Output")

    if run and chapter_text.strip():
        chapter["versions"].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": chapter_text
        })

        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "Story bible, timeline, and locked chapters are canon.\n\n"
            f"STORY BIBLE:\n{build_story_bible(sb)}\n\n"
            f"TIMELINE:\n{project['timeline']}"
        )

        if pov != "None":
            system_prompt += f"\n\nStrict POV: {pov}"
        if focus != "None":
            system_prompt += f"\n\nEmphasize emotional and narrative focus on {focus}."
        if tense != "Keep Original":
            system_prompt += f"\n\nAll output must be strictly {tense.lower()} tense."

        if VOICE_PROFILES[voice]:
            system_prompt += f"\n\nSTYLE GUIDE:\n{VOICE_PROFILES[voice]}"

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{instruction_for(tool)}\n\nTEXT:\n{chapter_text}"}
            ],
        )

        output = response.output_text
        st.text_area("Result", output, height=280)

        # Scene Cards
        with st.expander("🧩 Scene Cards"):
            for i, s in enumerate(split_scenes(output), 1):
                st.markdown(f"**Scene {i}**")
                st.text(s[:500])

        # Export
        doc = export_docx(chapter_name, output)
        st.download_button(
            "⬇ Export DOCX",
            doc._body._element.xml,
            file_name=f"{chapter_name}.docx"
        )
