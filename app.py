import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v3.0")

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
            "chapters": {
                "Chapter 1": ""
            }
        }
    }

projects = st.session_state.projects

# ================== VOICES ==================
VOICE_PROFILES = {
    "Default": "",
    "Literary": "Long sentences. Interior monologue. Metaphor. Controlled pacing.",
    "Minimal": "Short sentences. Subtext. Restraint. No excess description.",
    "Noir": "Hard edges. Dry voice. Concrete imagery. Cynical tone.",
    "Romantic": "Emotional language. Intimacy. Sensory focus.",
    "Epic": "Elevated diction. Grand scope. Mythic tone."
}

# ================== HELPERS ==================
def build_story_bible(sb):
    out = []
    if sb["title"]: out.append(f"Title: {sb['title']}")
    if sb["genre"]: out.append(f"Genre: {sb['genre']}")
    if sb["tone"]: out.append(f"Tone: {sb['tone']}")
    if sb["themes"]: out.append(f"Themes: {sb['themes']}")
    if sb["world_rules"]:
        out.append("World Rules / Canon:")
        out.append(sb["world_rules"])
    if sb["characters"]:
        out.append("Characters:")
        for c in sb["characters"]:
            out.append(f"- {c['name']}: {c['description']}")
    return "\n".join(out)

def instruction_for(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite for clarity, flow, and grammar.",
        "Describe": "Add richer sensory detail and emotion.",
        "Brainstorm": "Generate ideas or possible next plot beats.",
        "Proofread": "Correct grammar, spelling, and punctuation only."
    }[tool]

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_name = st.selectbox(
        "Project",
        list(projects.keys()),
        key="project_select"
    )

    if st.button("➕ New Project"):
        projects[f"Project {len(projects)+1}"] = {
            "story_bible": {
                "title": "", "genre": "", "tone": "",
                "themes": "", "world_rules": "", "characters": []
            },
            "chapters": {"Chapter 1": ""}
        }

    project = projects[project_name]
    sb = project["story_bible"]

    st.divider()
    st.header("📘 Story Bible")

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

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))

    if st.button("➕ New Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = ""

    chapter_text = st.text_area(
        "Chapter Text",
        value=chapters[chapter_name],
        height=350
    )

    # AUTOSAVE
    chapters[chapter_name] = chapter_text

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm", "Proofread"]
    )

    voice = st.selectbox("Voice", list(VOICE_PROFILES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run = st.button("Run")

with right:
    st.header("🤖 AI Output")

    if run and chapter_text.strip():
        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "You MUST follow the story bible exactly.\n\n"
            f"STORY BIBLE:\n{build_story_bible(sb)}"
        )

        if VOICE_PROFILES[voice]:
            system_prompt += f"\n\nSTYLE GUIDE:\n{VOICE_PROFILES[voice]}"

        with st.spinner("Writing…"):
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
