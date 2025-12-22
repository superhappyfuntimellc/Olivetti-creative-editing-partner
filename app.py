import streamlit as st
from openai import OpenAI

# ----------------- SETUP -----------------
client = OpenAI()

st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — Multi-Voice Edition")

# ----------------- STORY BIBLE -----------------
if "story_bible" not in st.session_state:
    st.session_state.story_bible = {
        "title": "",
        "genre": "",
        "tone": "",
        "themes": "",
        "world_rules": "",
        "characters": []
    }

def build_story_bible_prompt(sb):
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

# ----------------- VOICE PROFILES -----------------
VOICE_PROFILES = {
    "Default": "",
    "Literary": "Long sentences. Interior monologue. Metaphor. Controlled pacing.",
    "Minimal": "Short sentences. Subtext. Restraint. No excess description.",
    "Noir": "Hard edges. Dry voice. Concrete imagery. Cynical tone."
}

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.header("📘 Story Bible")
    sb = st.session_state.story_bible

    sb["title"] = st.text_input("Title", sb["title"])
    sb["genre"] = st.text_input("Genre", sb["genre"])
    sb["tone"] = st.text_input("Tone", sb["tone"])
    sb["themes"] = st.text_area("Themes", sb["themes"])
    sb["world_rules"] = st.text_area("World Rules / Canon", sb["world_rules"])

    st.subheader("Characters")
    name = st.text_input("Character name")
    desc = st.text_area("Character description")

    if st.button("Add / Update Character") and name.strip():
        sb["characters"] = [c for c in sb["characters"] if c["name"] != name]
        sb["characters"].append({"name": name, "description": desc})

    for c in sb["characters"]:
        st.markdown(f"**{c['name']}** — {c['description']}")

# ----------------- MAIN UI -----------------
left, right = st.columns(2)

with left:
    st.subheader("Your Writing")
    user_text = st.text_area("Write here", height=350, placeholder="Start writing…")

    tool = st.selectbox("Tool", ["Expand", "Rewrite", "Describe", "Brainstorm"])
    voice_name = st.selectbox("Voice Profile", list(VOICE_PROFILES.keys()))
    creativity = st.slider("Creativity", 0.0, 1.0, 0.7)

    run = st.button("Run")

# ----------------- PROMPT BUILDING -----------------
def build_instruction(tool: str) -> str:
    if tool == "Expand":
        return "Continue the text naturally. Do not summarize."
    if tool == "Rewrite":
        return "Rewrite the text with improved clarity and flow."
    if tool == "Describe":
        return "Rewrite with richer sensory detail and emotion."
    if tool == "Brainstorm":
        return "Generate creative ideas or possible next plot beats."
    return ""

# ----------------- OUTPUT -----------------
with right:
    st.subheader("AI Output")

    if run and user_text.strip():
        instruction = build_instruction(tool)
        story_bible_text = build_story_bible_prompt(sb)
        voice_sample = VOICE_PROFILES[voice_name]

        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "You MUST follow the story bible exactly.\n\n"
            f"STORY BIBLE:\n{story_bible_text}"
        )

        if voice_sample:
            system_prompt += f"\n\nSTYLE GUIDE:\n{voice_sample}"

        with st.spinner("Writing…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=creativity,
                input=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"{instruction}\n\nTEXT:\n{user_text}"
                    }
                ],
            )

        st.text_area("Result", value=response.output_text, height=400)
