import streamlit as st
from openai import OpenAI

# ================== SETUP ==================
client = OpenAI()

st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — v1.0")

# ================== STORY BIBLE ==================
if "story_bible" not in st.session_state:
    st.session_state.story_bible = {
        "title": "",
        "genre": "",
        "tone": "",
        "themes": "",
        "world_rules": "",
        "characters": []
    }

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
        out.append("World Rules:")
        out.append(sb["world_rules"])
    if sb["characters"]:
        out.append("Characters:")
        for c in sb["characters"]:
            out.append(f"- {c['name']}: {c['description']}")
    return "\n".join(out)

# ================== VOICES ==================
VOICE_PROFILES = {
    "Default": "",
    "Literary": "Long sentences. Interior monologue. Metaphor. Controlled pacing.",
    "Minimal": "Short sentences. Subtext. Restraint.",
    "Noir": "Hard edges. Dry voice. Concrete imagery."
}

# ================== SIDEBAR ==================
with st.sidebar:
    st.header("📘 Story Bible")
    sb = st.session_state.story_bible

    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("Characters")
    name = st.text_input("Name")
    desc = st.text_area("Description")

    if st.button("Add Character") and name:
        sb["characters"].append({"name": name, "description": desc})

    for c in sb["characters"]:
        st.markdown(f"**{c['name']}** — {c['description']}")

# ================== MAIN UI ==================
left, right = st.columns(2)

with left:
    st.subheader("Your Writing")
    user_text = st.text_area("Write here", height=350)

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm"]
    )

    voice = st.selectbox("Voice", list(VOICE_PROFILES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run = st.button("Run")

def instruction(tool):
    return {
        "Expand": "Continue the text naturally. Do not summarize.",
        "Rewrite": "Rewrite with improved clarity and flow.",
        "Describe": "Add richer sensory detail and emotion.",
        "Brainstorm": "Generate ideas or possible next plot beats."
    }[tool]

# ================== OUTPUT ==================
with right:
    st.subheader("AI Output")

    if run and user_text.strip():
        story_bible = build_story_bible(sb)
        style = VOICE_PROFILES[voice]

        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "You MUST follow the story bible exactly.\n\n"
            f"STORY BIBLE:\n{story_bible}"
        )

        if style:
            system_prompt += f"\n\nSTYLE GUIDE:\n{style}"

        with st.spinner("Writing…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=creativity,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"{instruction(tool)}\n\nTEXT:\n{user_text}"
                    }
                ],
            )

        st.text_area("Result", response.output_text, height=400)
