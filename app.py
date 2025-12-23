import streamlit as st
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti 20.3 — Scene Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
def init_state():
    defaults = {
        "projects": {},
        "current_project": None,
        "current_scene": 0,
        "genre": "Literary",
        "pov": "Close Third",
        "tense": "Past",
        "persona": "Literary Guardian",
        "voice_memory": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# PRESETS
# ============================================================
GENRES = ["Literary", "Thriller", "Noir", "Comedy", "Lyrical"]
POVS = ["First", "Close Third", "Omniscient"]
TENSES = ["Past", "Present"]

PERSONAS = {
    "Literary Guardian": "Protects voice, subtlety, interiority.",
    "Brutal Line Editor": "Cuts excess, sharpens sentences.",
    "Structural Editor": "Focuses on scene purpose and pacing.",
    "Market-Aware Agent": "Flags clarity, stakes, genre signals."
}

# ============================================================
# HELPERS
# ============================================================
def new_scene(title="New Scene"):
    return {
        "title": title,
        "purpose": "",
        "tension": 0.5,
        "text": "",
        "comments": [],
        "versions": [],
    }

def save_version(scene):
    scene["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": scene["text"]
    })

def learn_voice(text):
    if len(text) > 300:
        st.session_state.voice_memory.append(text[:800])

def llm(system, prompt, temp=0.4):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def persona_comment(scene):
    prompt = f"""
EDITOR PERSONA:
{st.session_state.persona} — {PERSONAS[st.session_state.persona]}

GENRE: {st.session_state.genre}
POV: {st.session_state.pov}
TENSE: {st.session_state.tense}

SCENE PURPOSE:
{scene["purpose"]}

TEXT:
{scene["text"]}

Leave margin comments only. No rewriting.
"""
    comment = llm(
        "You are a professional editorial persona.",
        prompt,
        0.3
    )
    scene["comments"].append(comment)

# ============================================================
# SIDEBAR — PROJECT + ENGINE
# ============================================================
with st.sidebar:
    st.header("Olivetti Studio")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create Project") and name:
            st.session_state.projects[name] = {"scenes": [new_scene("Scene 1")]}
            st.session_state.current_project = name
            st.session_state.current_scene = 0
    else:
        st.session_state.current_project = choice

    st.divider()

    st.subheader("Global Style")
    st.selectbox("Genre", GENRES, key="genre")
    st.selectbox("POV", POVS, key="pov")
    st.selectbox("Tense", TENSES, key="tense")

    st.divider()

    st.subheader("Editorial Persona")
    st.selectbox("Persona", PERSONAS.keys(), key="persona")
    st.caption(PERSONAS[st.session_state.persona])

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 20.3")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
scenes = project["scenes"]

scene = scenes[st.session_state.current_scene]

left, center, right = st.columns([1.2, 3.5, 2.3])

# ============================================================
# LEFT — SCENE STRUCTURE
# ============================================================
with left:
    st.subheader("Scenes")

    for i, sc in enumerate(scenes):
        if st.button(sc["title"], key=f"s_{i}"):
            st.session_state.current_scene = i

    if st.button("Add Scene"):
        scenes.append(new_scene(f"Scene {len(scenes)+1}"))
        st.session_state.current_scene = len(scenes) - 1

# ============================================================
# CENTER — SCENE EDITOR
# ============================================================
with center:
    scene["title"] = st.text_input("Scene Title", scene["title"])
    scene["purpose"] = st.text_input("Scene Purpose", scene["purpose"])
    scene["tension"] = st.slider("Tension", 0.0, 1.0, scene["tension"])

    scene["text"] = st.text_area("", scene["text"], height=520)

    col1, col2 = st.columns(2)
    if col1.button("Save Version"):
        save_version(scene)
        learn_voice(scene["text"])

    if col2.button("Persona Comment"):
        persona_comment(scene)

# ============================================================
# RIGHT — COMMENTS
# ============================================================
with right:
    st.subheader("Editorial Comments")
    if not scene["comments"]:
        st.write("No comments yet.")
    for i, c in enumerate(scene["comments"]):
        st.markdown(f"**{st.session_state.persona} #{i+1}**")
        st.markdown(c)

st.caption("Olivetti 20.3 — Scene-First Authorial Engine")
