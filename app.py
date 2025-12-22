import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v4.0")

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
            "outline": "",
            "chapters": {
                "Chapter 1": {
                    "text": "",
                    "locked": False
                }
            }
        }
    }

projects = st.session_state.projects

# ================== VOICES ==================
VOICE_PROFILES = {
    "Default": "",
    "Literary": "Long sentences. Interior monologue. Metaphor. Controlled pacing.",
    "Minimal": "Short sentences. Subtext. Restraint.",
    "Noir": "Hard edges. Cynical tone. Concrete imagery.",
    "Romantic": "Emotional intimacy. Sensory focus.",
    "Epic": "Elevated diction. Mythic scale."
}

# ================== HELPERS ==================
def build_story_bible(sb):
    out = []
    for key, val in sb.items():
        if val:
            if isinstance(val, list):
                out.append("Characters:")
                for c in val:
                    out.append(f"- {c['name']}: {c['description']}")
            else:
                out.append(f"{key.replace('_',' ').title()}: {val}")
    return "\n".join(out)

def instruction_for(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite for clarity, flow, and style.",
        "Describe": "Enhance sensory detail and emotion.",
        "Brainstorm": "Generate ideas or plot options.",
        "Proofread": "Fix grammar, spelling, and punctuation only.",
        "Diagnostics": "Analyze pacing, tension, clarity, and voice."
    }[tool]

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
            "chapters": {"Chapter 1": {"text": "", "locked": False}}
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
    cname = st.text_input("Name")
    cdesc = st.text_area("Description")
    if st.button("Add / Update Character") and cname:
        sb["characters"] = [c for c in sb["characters"] if c["name"] != cname]
        sb["characters"].append({"name": cname, "description": cdesc})

    for c in sb["characters"]:
        st.markdown(f"**{c['name']}** — {c['description']}")

    st.divider()
    st.header("🧭 Outline / Beats")
    project["outline"] = st.text_area(
        "Outline",
        project["outline"],
        height=200
    )

# ================== MAIN ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))
    chapter = chapters[chapter_name]

    if st.button("➕ New Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = {"text": "", "locked": False}

    locked = st.checkbox("🔒 Lock Chapter", value=chapter["locked"])
    chapter["locked"] = locked

    chapter_text = st.text_area(
        "Chapter Text",
        value=chapter["text"],
        height=350,
        disabled=locked
    )

    if not locked:
        chapter["text"] = chapter_text  # AUTO-SAVE

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm", "Proofread", "Diagnostics"]
    )

    voice = st.selectbox("Voice", list(VOICE_PROFILES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run = st.button("Run")

with right:
    st.header("🤖 AI Output")

    if run and chapter_text.strip():
        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "The story bible is canon and must be followed.\n\n"
            f"STORY BIBLE:\n{build_story_bible(sb)}"
        )

        if VOICE_PROFILES[voice]:
            system_prompt += f"\n\nSTYLE GUIDE:\n{VOICE_PROFILES[voice]}"

        with st.spinner("Processing…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=creativity,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"{instruction_for(tool)}\n\nTEXT:\n{chapter_text}"
                    }
                ],
            )

        st.text_area(
            "Result",
            value=response.output_text,
            height=400
        )

        st.download_button(
            "⬇ Download Result (.txt)",
            response.output_text,
            file_name=f"{chapter_name}_{tool}.txt"
        )
