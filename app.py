import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
client = OpenAI()
st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v2.0 (Projects & Chapters)")

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
    if sb["title"]:
        out.append(f"Title: {sb['title']}")
    if sb["genre"]:
        out.append(f"Genre: {sb['genre']}")
    if sb["tone"]:
        out.append(f"Tone: {sb['tone']}")
    if sb["themes"]:
        out.append(f"Themes: {sb['themes']}")
    if sb["world_rules"]:
        out.append("World Rules / Canon:")
        out.append(sb["world_rules"])_]()
