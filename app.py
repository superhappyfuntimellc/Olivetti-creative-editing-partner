import streamlit as st
from openai import OpenAI
from io import StringIO
import difflib

try:
    from docx import Document
    DOCX_OK = True
except:
    DOCX_OK = False

# ================= CONFIG =================
st.set_page_config(layout="wide")
st.title("📝 Pro Writer Suite — v12.0 (Intelligence + Voices)")

client = OpenAI()

# ================= STATE ==================
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
            "chapter_summaries": {},
            "voices": {},
            "chapters": {"Chapter 1": ""}
        }
    }

if "current_project" not in st.session_state:
    st.session_state.current_project = "New Project"

projects = st.session_state.projects
project = projects[st.session_state.current_project]

# ================= VOICE PRESETS =================
GENRE_VOICES = {
    "Neutral": "",
    "Comedy": "Light, timing-aware, playful phrasing. Humor through contrast and surprise.",
    "Noir": "Hard-boiled voice. Short sentences. Cynical tone. Concrete imagery.",
    "Lyrical": "Musical language. Metaphor-rich. Emotional interiority.",
    "Thriller": "Tight pacing. Suspense-forward. Controlled urgency.",
    "Ironic": "Detached but sharp. Observational humor. Subtext-driven."
}

# ================= HELPERS =================
def extract_text(upload):
    if upload.type == "text/plain":
        return StringIO(upload.getvalue().decode("utf-8")).read()
    if upload.type.endswith("wordprocessingml.document") and DOCX_OK:
        doc = Document(upload)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""

def build_story_bible(sb):
    out = []
    for k, v in sb.items():
        if not v:
            continue
        if isinstance(v, list):
            out.append("Characters:")
            for c in v:
                out.append(f"- {c['name']}: {c['description']}")
        else:
            out.append(f"{k.replace('_',' ').title()}: {v}")
    return "\n".join(out)

def plagiarism_check(text):
    sents = [s.strip() for s in text.split(".") if len(s.strip()) > 25]
    hits = 0
    for i in range(len(sents)):
        for j in range(i+1, len(sents)):
            if difflib.SequenceMatcher(None, sents[i], sents[j]).ratio() > 0.85:
                hits += 1
    if hits > 6:
        return "HIGH", hits
    if hits > 3:
        return "MEDIUM", hits
    return "LOW", hits

def auto_outline(text):
    return client.responses.create(
        model="gpt-4.1-mini",
        input=f"Create a concise story outline from this chapter:\n\n{text}"
    ).output_text

def chapter_summary(text):
    return client.responses.create(
        model="gpt-4.1-mini",
        input=f"Summarize this chapter in 3–4 sentences:\n\n{text}"
    ).output_text

def instruction(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite for clarity, flow, and quality.",
        "Describe": "Add vivid sensory detail and emotion.",
        "Brainstorm": "Generate ideas, beats, or directions.",
        "Grammar": "Fix grammar, spelling, and punctuation only."
    }[tool]

# ================= SIDEBAR =================
with st.sidebar:
    st.header("📁 Projects")

    names = list(projects.keys())
    selected = st.selectbox(
        "Active Project",
        names,
        index=names.index(st.session_state.current_project)
    )
    st.session_state.current_project = selected
    project = projects[selected]

    new_project = st.text_input("New project name")
    if st.button("➕ Add Project") and new_project:
        projects[new_project] = {
            "story_bible": {
                "title": "", "genre": "", "tone": "",
                "themes": "", "world_rules": "", "characters": []
            },
            "outline": "",
            "chapter_summaries": {},
            "voices": {},
            "chapters": {"Chapter 1": ""}
        }
        st.session_state.current_project = new_project

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
    if st.button("Add Character") and cname:
        sb["characters"].append({"name": cname, "description": cdesc})

    st.divider()
    st.header("🎭 Voices")

    voice_name = st.text_input("New voice name")
    sample = st.text_area("Paste writing sample")
    if st.button("Save Voice") and voice_name and sample:
        project["voices"][voice_name] = sample

    if project["voices"]:
        st.caption("Saved voices:")
        for v in project["voices"]:
            st.write(f"• {v}")

# ================= MAIN ====================
left, right = st.columns(2)

with left:
    st.header("✍️ Writing")

    chapters = project["chapters"]
    chap = st.selectbox("Chapter", list(chapters.keys()))

    new_chap = st.text_input("New chapter name")
    if st.button("Add Chapter") and new_chap:
        chapters[new_chap] = ""
        chap = new_chap

    text = st.text_area("Chapter Text", chapters[chap], height=300)
    chapters[chap] = text

    upload = st.file_uploader("Import TXT / DOCX", type=["txt", "docx"])
    if upload:
        imported = extract_text(upload)
        if imported:
            chapters[chap] = imported

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm", "Grammar"]
    )

    tense = st.selectbox("Tense", ["Past", "Present"])
    genre_style = st.selectbox("Genre Style", list(GENRE_VOICES.keys()))

    custom_voice = st.selectbox(
        "Custom Voice",
        ["None"] + list(project["voices"].keys())
    )

    blend = st.slider("Custom Voice Blend", 0.0, 1.0, 0.5)

    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)
    run = st.button("Run AI")

with right:
    st.header("🧭 Outline & Intelligence")

    if st.button("🧠 Auto-Generate Outline") and text.strip():
        project["outline"] = auto_outline(text)

    project["outline"] = st.text_area(
        "Outline / Beats",
        project["outline"],
        height=200
    )

    if st.button("📌 Update Chapter Summary") and text.strip():
        project["chapter_summaries"][chap] = chapter_summary(text)

    if project["chapter_summaries"].get(chap):
        st.caption("Chapter summary:")
        st.write(project["chapter_summaries"][chap])

    if run and text.strip():
        bible = build_story_bible(project["story_bible"])

        voice_text = ""
        if custom_voice != "None":
            voice_text = project["voices"][custom_voice]

        system_prompt = f"""
You are a professional novelist.
Write in {tense} tense.
Genre style: {genre_style}.
Blend custom voice at {int(blend*100)}%.

STORY BIBLE:
{bible}

GENRE STYLE GUIDE:
{GENRE_VOICES[genre_style]}

CUSTOM VOICE SAMPLE:
{voice_text}
"""

        response = client.responses.create(
            model="gpt-4.1-mini",
            temperature=creativity,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{instruction(tool)}\n\n{text}"}
            ],
        )

        output = response.output_text

        st.subheader("🤖 AI Output")
        st.text_area("Result", value=output, height=300)

        risk, hits = plagiarism_check(output)
        st.caption(f"🕵️ Plagiarism signal: {risk} ({hits} repeats)")
