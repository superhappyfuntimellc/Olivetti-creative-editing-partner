import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
st.set_page_config(layout="wide")
st.title("🖋️ Olivetti — Writing Studio")

client = OpenAI()

# ================== STATE ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "My First Project": {
            "story_bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world_rules": "",
                "characters": []
            },
            "outline": "",
            "chapters": ["Chapter 1"],
            "chapter_texts": {"Chapter 1": ""},
            "style_sample": ""
        }
    }

if "current_project" not in st.session_state:
    st.session_state.current_project = "My First Project"

projects = st.session_state.projects
project = projects[st.session_state.current_project]

# ================== HELPERS ==================
def story_bible_text(sb):
    out = []
    for k, v in sb.items():
        if isinstance(v, list):
            if v:
                out.append("Characters:")
                for c in v:
                    out.append(f"- {c['name']}: {c['description']}")
        elif v:
            out.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(out)

def ai_call(system, user, temp=0.6):
    r = client.responses.create(
        model="gpt-4.1-mini",
        temperature=temp,
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]
    )
    return r.output_text

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📁 Projects")

    st.session_state.current_project = st.selectbox(
        "Select Project",
        list(projects.keys()),
        index=list(projects.keys()).index(st.session_state.current_project)
    )

    new_project = st.text_input("New Project Name")
    if st.button("Add Project") and new_project:
        projects[new_project] = {
            "story_bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world_rules": "",
                "characters": []
            },
            "outline": "",
            "chapters": ["Chapter 1"],
            "chapter_texts": {"Chapter 1": ""},
            "style_sample": ""
        }
        st.session_state.current_project = new_project

    st.divider()

    st.header("📘 Story Bible")
    sb = project["story_bible"]
    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.selectbox(
        "Genre",
        ["", "Comedy", "Noir", "Thriller", "Lyrical", "Ironic"],
        index=0
    )
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("Characters")
    cname = st.text_input("Name")
    cdesc = st.text_area("Description")
    if st.button("Add Character") and cname:
        sb["characters"].append({"name": cname, "description": cdesc})

    st.divider()
    st.header("🧭 Outline")
    project["outline"] = st.text_area("Outline / Beats", project["outline"], height=200)

# ================== MAIN ==================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapter = st.selectbox("Chapter", project["chapters"])

    project["chapter_texts"][chapter] = st.text_area(
        "Chapter Text",
        project["chapter_texts"][chapter],
        height=350
    )

    st.subheader("Chapter Tools")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ Add Chapter"):
            new_ch = f"Chapter {len(project['chapters']) + 1}"
            project["chapters"].append(new_ch)
            project["chapter_texts"][new_ch] = ""

    with col2:
        rename = st.text_input("Rename Chapter")
        if st.button("Rename") and rename:
            idx = project["chapters"].index(chapter)
            project["chapters"][idx] = rename
            project["chapter_texts"][rename] = project["chapter_texts"].pop(chapter)

    st.subheader("Find & Replace")
    find = st.text_input("Find")
    replace = st.text_input("Replace")
    if st.button("Replace All") and find:
        project["chapter_texts"][chapter] = project["chapter_texts"][chapter].replace(find, replace)

    st.subheader("Match My Writing Style")
    project["style_sample"] = st.text_area(
        "Paste your writing here",
        project["style_sample"],
        height=120
    )

    tense = st.selectbox("Tense", ["Keep", "Past", "Present"])

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Polish (Grammar)", "Brainstorm"]
    )

    run = st.button("Run AI")

with right:
    st.header("🤖 AI Output")

    if run and project["chapter_texts"][chapter]:
        system = "You are a professional novelist assistant.\n"
        system += "Follow the story bible exactly.\n\n"
        system += story_bible_text(project["story_bible"])

        if project["style_sample"]:
            system += "\n\nMatch this writing style:\n" + project["style_sample"]

        user = f"{tool} this text.\n"
        if tense != "Keep":
            user += f"Convert to {tense.lower()} tense.\n"
        user += "\nTEXT:\n" + project["chapter_texts"][chapter]

        with st.spinner("Writing…"):
            result = ai_call(system, user)

        st.text_area("Result", result, height=400)

