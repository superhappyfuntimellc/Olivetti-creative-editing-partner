import streamlit as st
from datetime import datetime
from statistics import mean
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Olivetti 20.5 — Parallel Drafts",
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
        "current_draft": "Core",
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
DRAFTS = ["Core", "Experimental", "Conservative"]
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
        "drafts": {
            "Core": "",
            "Experimental": "",
            "Conservative": "",
        },
        "versions": [],
        "voice_warnings": {},
    }

def save_version(scene, draft):
    scene["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "draft": draft,
        "text": scene["drafts"][draft]
    })

def learn_voice(text):
    if len(text) > 300:
        st.session_state.voice_memory.append(text[:800])

def sentence_lengths(text):
    sentences = [s.strip() for s in text.replace("?", ".").replace("!", ".").split(".") if s.strip()]
    return [len(s.split()) for s in sentences]

def voice_metrics(text):
    lengths = sentence_lengths(text)
    if not lengths:
        return 0.0, 0.0
    avg_len = mean(lengths)
    variance = max(lengths) - min(lengths)
    alignment = max(0.0, min(1.0, 1 - abs(avg_len - 18) / 18))
    drift = min(1.0, variance / 30)
    return alignment, drift

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

def rewrite_for_draft(scene, draft):
    persona_weight = PERSONAS[st.session_state.persona]
    workflow_pressure = WORKFLOWS.index(st.session_state.workflow) / (len(WORKFLOWS) - 1)

    if draft == "Experimental":
        strictness = max(0.1, 0.4 - workflow_pressure)
    elif draft == "Conservative":
        strictness = min(1.0, 0.8 + workflow_pressure)
    else:
        strictness = 0.6

    prompt = f"""
Rewrite this scene.

TARGET DRAFT: {draft}
PERSONA: {st.session_state.persona}
STRICTNESS: {strictness}

AUTHOR VOICE:
{chr(10).join(st.session_state.voice_memory[-5:])}

TEXT:
{scene["drafts"]["Core"]}
"""
    scene["drafts"][draft] = llm(
        "You are an elite fiction editor preserving authorial intent.",
        prompt,
        0.5
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
    st.selectbox("Workflow", WORKFLOWS, key="workflow")
    st.selectbox("Persona", PERSONAS.keys(), key="persona")
    st.selectbox("Active Draft", DRAFTS, key="current_draft")

# ============================================================
# MAIN
# ============================================================
if not st.session_state.current_project:
    st.title("Olivetti 20.5")
    st.write("Create or select a project to begin.")
    st.stop()

project = st.session_state.projects[st.session_state.current_project]
scenes = project["scenes"]
scene = scenes[st.session_state.current_scene]
draft = st.session_state.current_draft

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
# CENTER — DRAFT EDITOR
# ============================================================
with center:
    scene["title"] = st.text_input("Scene Title", scene["title"])
    scene["purpose"] = st.text_input("Scene Purpose", scene["purpose"])

    scene["drafts"][draft] = st.text_area(
        f"{draft} Draft",
        scene["drafts"][draft],
        height=560
    )

    col1, col2, col3 = st.columns(3)
    if col1.button("Save Version"):
        save_version(scene, draft)
        if draft == "Core":
            learn_voice(scene["drafts"][draft])

    if col2.button("Generate Experimental"):
        rewrite_for_draft(scene, "Experimental")

    if col3.button("Generate Conservative"):
        rewrite_for_draft(scene, "Conservative")

# ============================================================
# RIGHT — COMPARISON + RADAR
# ============================================================
with right:
    st.subheader("Draft Comparison")

    for d in DRAFTS:
        alignment, drift = voice_metrics(scene["drafts"][d])
        st.markdown(f"**{d}**")
        st.progress(alignment)
        st.caption(f"Alignment {int(alignment*100)}% · Drift {int(drift*100)}%")

    st.divider()
    st.subheader("Merge Control")

    target = st.selectbox("Promote to Core", ["Experimental", "Conservative"])
    if st.button("Replace Core with Selected"):
        scene["drafts"]["Core"] = scene["drafts"][target]
        save_version(scene, "Core")
        learn_voice(scene["drafts"]["Core"])

st.caption("Olivetti 20.5 — Parallel Draft States")
