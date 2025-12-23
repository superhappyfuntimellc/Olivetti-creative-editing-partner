import streamlit as st
from datetime import datetime
from openai import OpenAI
import statistics
import re

st.set_page_config(layout="wide", page_title="🫒 Olivetti 19.5 — Voice Authority")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
defaults = {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "strictness": 0.4,  # 0=draft, 1=final
    "comments": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# ANALYZER
# =========================
def analyze_text(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    lengths = [len(s.split()) for s in sentences]

    return {
        "sentence_mean": statistics.mean(lengths) if lengths else 0,
        "sentence_var": statistics.pvariance(lengths) if len(lengths) > 1 else 0,
        "dialogue_ratio": len(re.findall(r'"', text)) / max(len(text), 1),
        "metaphor_hits": len(re.findall(r'\blike\b|\bas\b', text.lower())),
        "length": len(text)
    }

def score_against_profile(metrics, profile):
    if not profile:
        return 1.0, []

    notes = []
    score = 1.0

    for k in profile:
        diff = abs(metrics[k] - profile[k])
        if diff > profile[k] * 0.25:
            score -= 0.2
            notes.append(f"{k.replace('_',' ')} drift")

    return max(score, 0), notes

# =========================
# VOICE TRAINING
# =========================
def update_voice_profile(project):
    strong = project["voice_samples"]
    if not strong:
        return

    agg = {}
    for s in strong:
        m = analyze_text(s)
        for k, v in m.items():
            agg.setdefault(k, []).append(v)

    project["voice_profile"] = {
        k: statistics.mean(v) for k, v in agg.items()
    }

# =========================
# LLM CALL
# =========================
def call_llm(prompt):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a disciplined literary editor."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    return r.output_text

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("📁 Project")

    projects = list(st.session_state.projects.keys())
    choice = st.selectbox("Project", ["— New —"] + projects)

    if choice == "— New —":
        name = st.text_input("Project name")
        if st.button("Create") and name:
            st.session_state.projects[name] = {
                "chapters": [],
                "bible": "",
                "voice_profile": {},
                "voice_samples": []
            }
            st.session_state.current_project = name
    else:
        st.session_state.current_project = choice

    project = st.session_state.projects.get(st.session_state.current_project)

    if project:
        st.divider()
        st.subheader("🎤 Voice Training")
        exemplar = st.text_area("Paste strongest work", height=120)

        if st.button("Analyze & Add") and exemplar:
            metrics = analyze_text(exemplar)
            project["voice_samples"].append(exemplar)
            update_voice_profile(project)

            st.session_state.comments.append({
                "msg": "High-confidence passage added to voice profile",
                "details": metrics
            })

        st.divider()
        st.subheader("🎚 Voice Strictness")
        st.session_state.strictness = st.slider(
            "Draft → Final",
            0.0, 1.0, st.session_state.strictness
        )

# =========================
# MAIN
# =========================
if not project:
    st.title("🫒 Olivetti Studio")
    st.stop()

if not project["chapters"]:
    project["chapters"].append({
        "title": "Chapter 1",
        "text": "",
        "versions": []
    })

chapter = project["chapters"][st.session_state.current_chapter]

left, center, right = st.columns([1.2, 2.6, 2.2])

# =========================
# CENTER — TEXT
# =========================
with center:
    st.subheader("✍️ Chapter Text")
    chapter["text"] = st.text_area("", chapter["text"], height=520)

    if st.button("💾 Save Version"):
        chapter["versions"].append({
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "text": chapter["text"]
        })

# =========================
# RIGHT — ANALYZER FEEDBACK
# =========================
with right:
    st.subheader("💬 Editorial Comments")

    for c in st.session_state.comments[-5:]:
        with st.expander("Voice Analysis"):
            st.write(c["msg"])
            st.json(c["details"])

    st.divider()
    st.subheader("🧪 Rewrite with Enforcement")

    if st.button("Rewrite (Voice Locked)"):
        base = chapter["text"]
        rewritten = call_llm(f"Rewrite preserving voice:\n\n{base}")

        metrics = analyze_text(rewritten)
        score, notes = score_against_profile(metrics, project["voice_profile"])

        threshold = 0.6 + (st.session_state.strictness * 0.3)

        if score < threshold:
            st.session_state.comments.append({
                "msg": "⚠️ Voice drift detected — corrected",
                "details": notes
            })
        else:
            chapter["text"] = rewritten
            st.session_state.comments.append({
                "msg": "✔ Rewrite accepted (voice consistent)",
                "details": metrics
            })

st.caption("🫒 Olivetti 19.5 — voice is enforced, not suggested")
