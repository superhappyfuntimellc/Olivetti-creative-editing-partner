import streamlit as st

st.set_page_config(
    page_title="Olivetti",
    layout="wide"
)

# ======================
# SESSION STATE
# ======================
if "projects" not in st.session_state:
    st.session_state.projects = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

# ======================
# TOP BAR
# ======================
st.markdown("## 🫒 Olivetti — Digital Writing Desk")
st.divider()

# ======================
# SIDEBAR — PROJECTS
# ======================
with st.sidebar:
    st.header("📁 Projects")

    project_names = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + project_names)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {
                "chapters": [{"title": "Chapter 1", "text": ""}]
            }
            st.session_state.current_project = name
            st.session_state.current_chapter = 0
    else:
        st.session_state.current_project = choice

# ======================
# MAIN AREA
# ======================
if not st.session_state.current_project:
    st.info("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
chapters = project["chapters"]

# Guard index
if st.session_state.current_chapter >= len(chapters):
    st.session_state.current_chapter = 0

chapter = chapters[st.session_state.current_chapter]

left, center, right = st.columns([1.2, 2.6, 2.0])

# ======================
# LEFT — STORY BIBLE
# ======================
with left:
    st.subheader("📚 Story Bible")

    for i, ch in enumerate(chapters):
        if st.button(f"{i+1}. {ch['title']}", key=f"chap_{i}"):
            st.session_state.current_chapter = i

    st.divider()

    if st.button("➕ Add Chapter"):
        chapters.append({"title": f"Chapter {len(chapters)+1}", "text": ""})
        st.session_state.current_chapter = len(chapters) - 1

# ======================
# CENTER — WRITING DESK
# ======================
with center:
    st.subheader("✍️ Writing Desk")

    chapter["title"] = st.text_input("Chapter Title", chapter["title"])

    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=500
    )

    st.caption("Autosaves as you type")

# ======================
# RIGHT — VOICE BIBLE (STUB)
# ======================
with right:
    st.subheader("🎭 Voice Bible")

    st.selectbox(
        "Narrative Voice",
        ["Neutral", "Minimal", "Expressive", "Poetic", "Hardboiled"]
    )

    st.selectbox(
        "Genre",
        ["Literary", "Thriller", "Noir", "Comedy", "Lyrical"]
    )

    st.slider(
        "AI Intensity (coming next)",
        0.0, 1.0, 0.5
    )

    st.caption("Voice training + AI tools will attach here")

st.caption("Olivetti — foundation locked")
