import streamlit as st
from openai import OpenAI
from datetime import datetime

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v5.0")

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
    "Literary": "Long sentences. Interior monologue. Metaphor. Controlled pacing.",
    "Minimal": "Short sentences. Subtext. Restraint.",
    "Noir": "Hard edges. Cynical tone. Concrete imagery.",
    "Romantic": "Emotional intimacy. Sensory focus.",
    "Epic": "Elevated diction. Mythic scale."
}

# ================== HELPERS ==================
def build_story_bible(sb):
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
        "Rewrite": "Rewrite for clarity, flow, and style.",
        "Describe": "Add vivid sensory detail.",
        "Brainstorm": "Generate plot ideas or options.",
        "Proofread": "Fix grammar, spelling, and punctuation only.",
        "Diagnostics": "Analyze pacing, clarity, tension, POV, and consistency."
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
    cname = st.text_input("Name")
    cdesc = st.text_area("Description")
    if st.button("Add / Update Character") and cname:
        sb["characters"] = [c for c in sb["characters"] if c["name"] != cname]
        sb["characters"].append({"name": cname, "description": cdesc})

    st.divider()
    st.header("🧭 Outline")
    project["outline"] = st.text_area("Outline / Beats", project["outline"], height=150)

    st.header("⏱️ Timeline / Continuity")
    project["timeline"] = st.text_area("Timeline Notes", project["timeline"], height=120)

# ================== MAIN ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))
    chapter = chapters[chapter_name]

    if st.button("➕ New Chapter"):
        chapters[f"Chapter {len(chapters)+1}"] = {
            "text": "", "locked": False, "versions": []
        }

    locked = st.checkbox("🔒 Lock Chapter", chapter["locked"])
    chapter["locked"] = locked

    chapter_text = st.text_area(
        "Chapter Text",
        value=chapter["text"],
        height=350,
        disabled=locked
    )

    if not locked:
        chapter["text"] = chapter_text  # AUTOSAVE

    pov = st.selectbox(
        "POV Lock (optional)",
        ["None"] + [c["name"] for c in sb["characters"]]
    )

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
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        chapter["versions"].append({
            "time": timestamp,
            "text": chapter_text
        })

        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "Story bible and timeline are canon.\n\n"
            f"STORY BIBLE:\n{build_story_bible(sb)}\n\n"
            f"TIMELINE:\n{project['timeline']}"
        )

        if pov != "None":
            system_prompt += f"\n\nWrite strictly from {pov}'s POV."

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

        output = response.output_text

        st.text_area("Result", output, height=300)

        with st.expander("🔍 Before / After Diff"):
            st.markdown("### BEFORE")
            st.text(chapter_text)
            st.markdown("### AFTER")
            st.text(output)

        with st.expander("🧬 Version History"):
            for v in reversed(chapter["versions"][-10:]):
                st.markdown(f"**{v['time']}**")
                st.text(v["text"][:500])

        st.download_button(
            "⬇ Download Result",
            output,
            file_name=f"{chapter_name}_{tool}.txt"
        )
