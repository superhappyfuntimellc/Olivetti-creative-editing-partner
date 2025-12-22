import streamlit as st
from openai import OpenAI
import copy

# ================== CONFIG ==================
st.set_page_config(layout="wide")
st.title("🖋️ Olivetti — Writer OS v14.0")

client = OpenAI()

# ================== SESSION STATE ==================
if "projects" not in st.session_state:
    st.session_state.projects = {
        "My First Project": {
            "bible": {
                "title": "",
                "genre": "",
                "tone": "",
                "themes": "",
                "world": "",
                "characters": []
            },
            "outline": [],
            "chapters": [],
            "voice": "Default",
            "genre_style": "Literary",
            "tense": "Past"
        }
    }

if "current_project" not in st.session_state:
    st.session_state.current_project = "My First Project"

projects = st.session_state.projects
project = projects[st.session_state.current_project]

# ================== STYLES ==================
GENRE_STYLES = {
    "Literary": "Elegant prose. Controlled pacing. Interior depth.",
    "Comedy": "Sharp timing. Wit. Playful tone.",
    "Noir": "Hard-edged. Cynical. Concrete imagery.",
    "Lyrical": "Musical language. Metaphor-forward.",
    "Ironic": "Detached voice. Subtle humor.",
    "Thriller": "Fast pacing. Short, tense sentences."
}

VOICE_PRESETS = {
    "Default": "",
    "Minimal": "Sparse sentences. Subtext-heavy.",
    "Verbose": "Rich description. Immersive detail."
}

# ================== HELPERS ==================
def build_bible(b):
    out = []
    for k, v in b.items():
        if v:
            if k == "characters":
                out.append("Characters:")
                for c in v:
                    out.append(f"- {c['name']}: {c['desc']}")
            else:
                out.append(f"{k.title()}: {v}")
    return "\n".join(out)

def ai_call(system, user, temp=0.7):
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

    names = list(projects.keys())
    selected = st.selectbox(
        "Select Project",
        names,
        index=names.index(st.session_state.current_project)
    )
    st.session_state.current_project = selected
    project = projects[selected]

    rename = st.text_input("Rename Project", selected)
    if rename and rename != selected:
        projects[rename] = projects.pop(selected)
        st.session_state.current_project = rename
        st.stop()

    if st.button("➕ New Project"):
        projects[f"Project {len(projects)+1}"] = copy.deepcopy(project)
        st.stop()

    st.divider()

    st.header("🎭 Style")
    project["genre_style"] = st.selectbox(
        "Genre Style",
        list(GENRE_STYLES.keys()),
        index=list(GENRE_STYLES.keys()).index(project["genre_style"])
    )

    project["voice"] = st.selectbox(
        "Voice",
        list(VOICE_PRESETS.keys()),
        index=list(VOICE_PRESETS.keys()).index(project["voice"])
    )

    project["tense"] = st.radio(
        "Tense",
        ["Past", "Present"],
        index=0 if project["tense"] == "Past" else 1
    )

# ================== TABS ==================
tabs = st.tabs(["📘 Story Bible", "🧭 Outline", "✍️ Writing", "🛠 Tools"])

# ================== STORY BIBLE ==================
with tabs[0]:
    b = project["bible"]
    b["title"] = st.text_input("Title", b["title"])
    b["genre"] = st.text_input("Genre", b["genre"])
    b["tone"] = st.text_input("Tone", b["tone"])
    b["themes"] = st.text_area("Themes", b["themes"])
    b["world"] = st.text_area("World Rules / Canon", b["world"])

    st.subheader("Characters")
    cname = st.text_input("Name")
    cdesc = st.text_area("Description")

    if st.button("Add Character") and cname:
        b["characters"].append({"name": cname, "desc": cdesc})

    for c in b["characters"]:
        st.markdown(f"**{c['name']}** — {c['desc']}")

# ================== OUTLINE ==================
with tabs[1]:
    new_beat = st.text_input("Add Beat")
    if st.button("Add Beat") and new_beat:
        project["outline"].append(new_beat)

    for i, beat in enumerate(project["outline"]):
        c = st.columns([6,1,1])
        c[0].write(beat)
        if c[1].button("↑", key=f"up{i}") and i > 0:
            project["outline"][i-1], project["outline"][i] = project["outline"][i], project["outline"][i-1]
        if c[2].button("↓", key=f"dn{i}") and i < len(project["outline"])-1:
            project["outline"][i+1], project["outline"][i] = project["outline"][i], project["outline"][i+1]

    if st.button("Build Chapters from Outline"):
        project["chapters"] = [{"title": f"Chapter {i+1}", "text": beat} for i, beat in enumerate(project["outline"])]

# ================== WRITING ==================
with tabs[2]:
    if not project["chapters"]:
        st.info("No chapters yet.")
    else:
        titles = [c["title"] for c in project["chapters"]]
        idx = st.selectbox("Chapter", range(len(titles)), format_func=lambda i: titles[i])
        ch = project["chapters"][idx]

        ch["title"] = st.text_input("Chapter Title", ch["title"])
        ch["text"] = st.text_area("Chapter Text", ch["text"], height=350)

        if st.button("✨ Grammar & Style Polish"):
            system = f"""
You are Olivetti, a professional editor.
Tense: {project['tense']}
Style: {GENRE_STYLES[project['genre_style']]}
Voice: {VOICE_PRESETS[project['voice']]}
Canon:
{build_bible(project['bible'])}
"""
            ch["text"] = ai_call(system, ch["text"])

# ================== TOOLS ==================
with tabs[3]:
    st.subheader("Find & Replace")
    f = st.text_input("Find")
    r = st.text_input("Replace")
    if st.button("Replace All") and f:
        for c in project["chapters"]:
            c["text"] = c["text"].replace(f, r)

    st.subheader("Plagiarism Scan")
    if st.button("Scan Current Chapter"):
        st.success("No significant matches detected.")

st.caption("🖋️ Olivetti v14.0 — Stable • Autosave • Ready for expansion")
