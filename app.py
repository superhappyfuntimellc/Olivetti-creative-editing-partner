import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
client = OpenAI()
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v3.1 (Projects, Chapters, Grammar)")

# ================== DATA MODEL ==================
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
        "Rewrite": "Rewrite with improved clarity and flow.",
        "Describe": "Add richer sensory detail and emotion.",
        "Brainstorm": "Generate ideas or possible next plot beats."
    }[tool]

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    project_name = st.selectbox(
        "Project",
        list(projects.keys())
    )
    project = projects[project_name]

    if st.button("➕ New Project"):
        projects[f"Project {len(projects)+1}"] = {
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

    st.subheader("🧍 Characters")
    cname = st.text_input("Character name")
    cdesc = st.text_area("Character description")

    if st.button("Add / Update Character") and cname:
        sb["characters"] = [c for c in sb["characters"] if c["name"] != cname]
        sb["characters"].append({"name": cname, "description": cdesc})

    for c in sb["characters"]:
        st.markdown(f"**{c['name']}** — {c['description']}")

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
    chapter_name = st.selectbox("Chapter", list(chapters.keys()))

    chapter_text = st.text_area(
        "Chapter Text (spellcheck enabled)",
        chapters[chapter_name],
        height=400,
        help="Browser spellcheck is active"
    )

    # AUTO-SAVE
    chapters[chapter_name] = chapter_text

    new_chapter = st.text_input("New chapter name")
    if st.button("Add Chapter") and new_chapter:
        chapters[new_chapter] = ""

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm"]
    )

    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run_ai = st.button("Run AI")
    fix_grammar = st.button("Fix Grammar & Clarity")

# ================== OUTPUT ==================
with right:
    st.header("🤖 AI Output")

    story_bible_text = build_story_bible(sb)

    system_base = (
        "You are a professional creative writing assistant.\n"
        "Follow the story bible exactly.\n\n"
        f"STORY BIBLE:\n{story_bible_text}"
    )

    if run_ai and chapter_text.strip():
        with st.spinner("Writing…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=creativity,
                input=[
                    {"role": "system", "content": system_base},
                    {
                        "role": "user",
                        "content": f"{instruction_for(tool)}\n\nTEXT:\n{chapter_text}"
                    }
                ],
            )

        st.text_area("Result", response.output_text, height=400)

    if fix_grammar and chapter_text.strip():
        with st.spinner("Fixing grammar…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=0.2,
                input=[
                    {"role": "system", "content": system_base},
                    {
                        "role": "user",
                        "content": (
                            "Fix spelling, grammar, and clarity.\n"
                            "Preserve voice and meaning.\n\n"
                            f"TEXT:\n{chapter_text}"
                        )
                    }
                ],
            )

        chapters[chapter_name] = response.output_text
        st.success("Grammar fixed and auto-saved.")
