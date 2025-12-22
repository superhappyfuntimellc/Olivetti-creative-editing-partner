import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
client = OpenAI()
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v3.0 Stable")

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
            "chapters": {"Chapter 1": ""}
        }
    }

projects = st.session_state.projects

# ================== HELPERS ==================
def build_story_bible(sb):
    lines = []
    if sb["title"]: lines.append(f"Title: {sb['title']}")
    if sb["genre"]: lines.append(f"Genre: {sb['genre']}")
    if sb["tone"]: lines.append(f"Tone: {sb['tone']}")
    if sb["themes"]: lines.append(f"Themes: {sb['themes']}")
    if sb["world_rules"]:
        lines.append("World Rules / Canon:")
        lines.append(sb["world_rules"])
    if sb["characters"]:
        lines.append("Characters:")
        for c in sb["characters"]:
            lines.append(f"- {c['name']}: {c['description']}")
    return "\n".join(lines)

def instruction_for(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite with improved clarity and flow.",
        "Describe": "Add richer sensory detail and emotion.",
        "Brainstorm": "Generate plot ideas or next beats."
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

    st.subheader("🧍 Characters")
    cname = st.text_input("Character name")
    cdesc = st.text_area("Character description")
    if st.button("Add Character") and cname:
        sb["characters"].append({"name": cname, "description": cdesc})

    st.divider()
    project["outline"] = st.text_area(
        "🧭 Outline / Beats",
        project["outline"],
        height=200
    )

# ================== MAIN ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")
    chapters = project["chapters"]
    chapter = st.selectbox("Chapter", list(chapters.keys()))

    text = st.text_area(
        "Chapter Text (spellcheck enabled)",
        chapters[chapter],
        height=400
    )

    chapters[chapter] = text  # autosave

    new_chapter = st.text_input("New chapter name")
    if st.button("Add Chapter") and new_chapter:
        chapters[new_chapter] = ""

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm"]
    )

    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run_ai = st.button("Run AI")
    fix_grammar = st.button("Fix Grammar")

with right:
    st.header("🤖 AI Output")

    if (run_ai or fix_grammar) and text.strip():
        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "Follow the story bible exactly.\n\n"
            f"STORY BIBLE:\n{build_story_bible(sb)}"
        )

        user_prompt = (
            "Fix spelling, grammar, and clarity."
            if fix_grammar
            else instruction_for(tool)
        )

        with st.spinner("Thinking…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=0.2 if fix_grammar else creativity,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"{user_prompt}\n\n{text}"}
                ],
            )

        if fix_grammar:
            chapters[chapter] = response.output_text
            st.success("Grammar fixed and saved.")
        else:
            st.text_area("Result", response.output_text, height=400)
