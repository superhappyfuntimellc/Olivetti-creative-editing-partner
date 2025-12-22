import streamlit as st
import re

st.set_page_config(layout="wide", page_title="Olivetti v4.0")

# =========================
# SESSION STATE
# =========================
if "chapters" not in st.session_state:
    st.session_state.chapters = []
if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

# =========================
# HELPERS
# =========================
def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text, flags=re.IGNORECASE)
    chapters = []
    for i in range(1, len(parts), 2):
        title = parts[i].strip().title()
        body = parts[i + 1].strip()
        chapters.append({"title": title, "text": body})
    if not chapters:
        chapters.append({"title": "Chapter 1", "text": text})
    return chapters

def move_chapter(idx, direction):
    new_idx = idx + direction
    if 0 <= new_idx < len(st.session_state.chapters):
        st.session_state.chapters[idx], st.session_state.chapters[new_idx] = (
            st.session_state.chapters[new_idx],
            st.session_state.chapters[idx],
        )
        st.session_state.current_chapter = new_idx

# =========================
# SIDEBAR — MANUSCRIPT CONTROL
# =========================
with st.sidebar:
    st.header("📘 Manuscript")

    uploaded = st.file_uploader("Import manuscript (.txt)", type=["txt"])
    if uploaded:
        text = uploaded.read().decode("utf-8")
        st.session_state.chapters = split_into_chapters(text)
        st.session_state.current_chapter = 0

    st.divider()

    if st.session_state.chapters:
        for i, ch in enumerate(st.session_state.chapters):
            if st.button(f"{i+1}. {ch['title']}", key=f"ch_{i}"):
                st.session_state.current_chapter = i

# =========================
# MAIN LAYOUT
# =========================
if not st.session_state.chapters:
    st.title("🫒 Olivetti")
    st.write("Import a manuscript to begin.")
    st.stop()

left, right = st.columns([2, 3])

# =========================
# LEFT — OUTLINE / STRUCTURE
# =========================
with left:
    st.subheader("🧭 Outline")

    idx = st.session_state.current_chapter
    chapter = st.session_state.chapters[idx]

    chapter["title"] = st.text_input("Chapter title", chapter["title"])

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬆ Move Up"):
            move_chapter(idx, -1)
    with col2:
        if st.button("⬇ Move Down"):
            move_chapter(idx, 1)

    st.divider()

    find = st.text_input("Find")
    replace = st.text_input("Replace")
    if st.button("Replace in chapter") and find:
        chapter["text"] = chapter["text"].replace(find, replace)

# =========================
# RIGHT — WRITING VIEW
# =========================
with right:
    st.subheader("✍️ Chapter Text")

    chapter["text"] = st.text_area(
        "",
        chapter["text"],
        height=500
    )

    st.caption("Autosaved in session. No buttons needed.")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Olivetti v4.0 — Writer-first manuscript workspace")
