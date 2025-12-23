import streamlit as st
from datetime import datetime
from statistics import mean
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti 20.4 — Live Voice Radar",
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
        "workflow": "Draft",
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
WORKFLOWS = ["Draft", "Revise", "Polish", "Final"]

PERSONAS = {
    "Literary Guardian": 0.9,
    "Brutal Line Editor": 1.0,
    "Structural Editor": 0.7,
    "Market-Aware Agent": 0.8,
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
        "voice_warnings": "",
    }

def save_version(scene):
    scene["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": scene["text"]
    })

def learn_voice(text):
    if len(text) > 300:
        st.session_state.voice_memory.append(text[:800])

def sentence_lengths(text):
    sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    return [len(s.split()) for s in sentences]

def voice_radar(scene_text):
    lengths = sentence_lengths(scene_text)
    if not lengths:
        return 0.0, 0.0

    avg_len = mean(lengths)
    variance = max(lengths) - min(lengths)

    alignment = max(0.0, min(1.0, 1 - abs(avg_len - 18) / 18))
    drift = min(1.0, variance / 30)

    return alignment, drift

def llm(system, prompt, temp=0.3):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def deep_voice_check(scene):
    prompt = f"""
Compare this scene to the author's established voice.
Flag specific deviations if present.

AUTHOR VOICE:
{chr(10).join(st.session_state.voice_memory[-5:])}

TEXT:
{scene["text"]}
"""
    scene["voice_warnings"] = llm(
        "You are a literary continuity editor.",
        prompt
    )

# ============================================================
# SIDEBAR
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
    st.selectbox("Genre", GENRES, key="genre")
    st.selectbox("POV", POVS, key="pov")
    st.selectbox("Tense", TENSES, key="tense")
    st.selectbox("Workflow", WORKFLOWS, key="workflow")
    st.selectbox("Persona", PERSONAS.keys(), key="persona")

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 20.4")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
scenes = project["scenes"]
scene = scenes[st.session_state.current_scene]

left, center, right = st.columns([1.1, 3.4, 2.0])

# ============================================================
# LEFT — SCENES
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
# CENTER — WRITE
# ============================================================
with center:
    scene["title"] = st.text_input("Scene Title", scene["title"])
    scene["purpose"] = st.text_input("Scene Purpose", scene["purpose"])
    scene["text"] = st.text_area("", scene["text"], height=560)

    if st.button("Save Version"):
        save_version(scene)
        learn_voice(scene["text"])

# ============================================================
# RIGHT — LIVE VOICE RADAR
# ============================================================
with right:
    st.subheader("Live Voice Radar")

    alignment, drift = voice_radar(scene["text"])

    persona_weight = PERSONAS[st.session_state.persona]
    workflow_pressure = WORKFLOWS.index(st.session_state.workflow) / (len(WORKFLOWS)-1)

    st.metric("Voice Alignment", f"{int(alignment*100)}%")
    st.metric("Drift Risk", f"{int(drift*100)}%")
    st.metric("Persona Sensitivity", f"{int(persona_weight*100)}%")
    st.metric("Workflow Pressure", f"{int(workflow_pressure*100)}%")

    st.progress(alignment)
    st.progress(drift)

    if st.button("Deep Voice Check"):
        deep_voice_check(scene)

    if scene["voice_warnings"]:
        st.subheader("Voice Warnings")
        st.write(scene["voice_warnings"])

st.caption("Olivetti 20.4 — Live Voice Radar")
