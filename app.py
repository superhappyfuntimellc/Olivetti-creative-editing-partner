import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v12.0")

client = OpenAI()

# ================== SESSION STATE ==================
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
                "Chapter 1": ""
            }
        }
    }

projects = st.session_state.projects

# ================== HELPERS ==================
def build_story_bible(sb):
    lines = []
    for k, v in sb.items():
        if not v:
            continue
        if isinstance(v, list):
            lines.append("Characters:")
            for c in v:
                lines.append(f"- {c['name']}: {c['description']}")
        else:
            lines.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(lines)

STYLE_GUIDES = {
    "Comedy": "Witty, sharp, humorous. Timing matters.",
    "Noir": "Hardboiled, cynical, concrete imagery.",
    "Lyrical": "Musical language, metaphor, emotion.",
    "Ironic": "Detached, clever, understated.",
    "Thriller": "Fast-paced, tense, high stakes."
}

TOOLS = {
    "Expand": "Continue the text naturally.",
    "Rewrite": "Rewrite with improved clarity and flow.",
    "Describe": "Add richer sensory detail.",
    "Brainstorm": "Generate ideas or next plot beats."
}

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_name = st.selectbox(
        "Select Project",
        list(projects.keys())
    )
    project = projects[project_name]

    new_project_name = st.text_input("New project name")
    if st.button("➕ Add Project") and new_project_name:
        projects[new_project_name] = {
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

    st.divider()

    st.header("📘 Story Bible")
    sb = project["story_bible"]

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

    st.header("🧭 Outline")
    project["outline"] = st.text_area(
        "Outline / Beats",
        project["outline"],
        height=200
    )

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chapter_names = list(chapters.keys())
    chapter_name = st.selectbox("Chapter", chapter_names)

    # Reorder
    col1, col2 = st.columns(2)
    idx = chapter_names.index(chapter_name)

    if col1.button("⬆ Move Up") and idx > 0:
        chapter_names[idx], chapter_names[idx-1] = chapter_names[idx-1], chapter_names[idx]
        project["chapters"] = {k: chapters[k] for k in chapter_names}

    if col2.button("⬇ Move Down") and idx < len(chapter_names)-1:
        chapter_names[idx], chapter_names[idx+1] = chapter_names[idx+1], chapter_names[idx]
        project["chapters"] = {k: chapters[k] for k in chapter_names}

    new_chapter = st.text_input("New chapter name")
    if st.button("Add Chapter") and new_chapter:
        chapters[new_chapter] = ""

    chapters[chapter_name] = st.text_area(
        "Chapter Text",
        chapters[chapter_name],
        height=400
    )

    st.subheader("🔍 Find & Replace")
    find = st.text_input("Find")
    replace = st.text_input("Replace")
    if st.button("Replace All") and find:
        chapters[chapter_name] = chapters[chapter_name].replace(find, replace)

with right:
    st.header("🤖 AI Tools")

    tool = st.selectbox("Tool", list(TOOLS.keys()))
    tense = st.selectbox("Tense", ["Present", "Past"])
    style = st.selectbox("Genre Style", list(STYLE_GUIDES.keys()))
    voice_sample = st.text_area("Author Voice Sample (optional)", height=120)
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    if st.button("Run AI"):
        system_prompt = f"""
You are a professional creative writing assistant.
Use {tense} tense.
Style guide: {STYLE_GUIDES[style]}

STORY BIBLE:
{build_story_bible(project['story_bible'])}
"""

        if voice_sample:
            system_prompt += f"\nAUTHOR STYLE SAMPLE:\n{voice_sample}"

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"{TOOLS[tool]}\n\nTEXT:\n{chapters[chapter_name]}"
                }
            ],
        )

        st.text_area(
            "AI Output",
            response.output_text,
            height=400
        )

    st.divider()
    st.subheader("🧪 Utilities")

    if st.button("Check Plagiarism"):
        st.info("Plagiarism checker placeholder — ready for API hookup.")

    if st.button("Spellcheck / Grammar"):
        st.info("Grammar tool placeholder — will run AI cleanup pass.")
