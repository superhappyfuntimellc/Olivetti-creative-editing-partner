import streamlit as st
from openai import OpenAI

# ----------------- SETUP -----------------
client = OpenAI()

st.set_page_config(layout="wide")
st.title("📝 Personal Sudowrite — Multi-Voice Edition")

# ----------------- VOICE PROFILES -----------------
VOICE_PROFILES = {
    "Default": "",
    "Literary": """Paste a sample of your literary-style writing here.
Longer sentences, interiority, metaphor, controlled pacing.""",

    "Minimal": """Paste a sample of your minimalist writing here.
Short sentences. Subtext. Restraint. No excess description.""",

    "Noir": """Paste a sample of your noir-style writing here.
Hard edges. Dry voice. Concrete imagery. Cynical tone."""
}

# ----------------- UI -----------------
left, right = st.columns(2)

with left:
    st.subheader("Your Writing")

    user_text = st.text_area(
        "Write here",
        height=350,
        placeholder="Start writing…"
    )

    tool = st.selectbox(
        "Tool",
        ["Expand", "Rewrite", "Describe", "Brainstorm"]
    )

    voice_name = st.selectbox(
        "Voice Profile",
        list(VOICE_PROFILES.keys())
    )

    creativity = st.slider(
        "Creativity",
        min_value=0.0,
        max_value=1.0,
        value=0.7
    )

    run = st.button("Run")

# ----------------- PROMPT BUILDING -----------------
def build_instruction(tool: str) -> str:
    if tool == "Expand":
        return (
            "Continue the text naturally.\n"
            "Match voice, tone, and pacing.\n"
            "Do not summarize or explain."
        )

    if tool == "Rewrite":
        return (
            "Rewrite the text with improved clarity and flow.\n"
            "Preserve meaning and voice."
        )

    if tool == "Describe":
        return (
            "Rewrite the text with richer sensory detail.\n"
            "Emphasize emotion, atmosphere, and specificity."
        )

    if tool == "Brainstorm":
        return (
            "Generate creative ideas, metaphors, or possible next plot beats.\n"
            "Be inventive but grounded in the given text."
        )

    return ""

# ----------------- OUTPUT -----------------
with right:
    st.subheader("AI Output")

    if run and user_text.strip():

        voice_sample = VOICE_PROFILES.get(voice_name, "")
        instruction = build_instruction(tool)

        system_prompt = (
            "You are a professional creative writing assistant.\n"
            "You produce polished, publication-quality prose."
        )

        if voice_sample.strip():
            system_prompt += (
                "\n\nWrite in the same *style* as the following author sample.\n"
                "Match rhythm, sentence length, tone, and stylistic tendencies.\n"
                "Do NOT imitate content, themes, or characters — style only.\n\n"
                f"AUTHOR STYLE SAMPLE:\n{voice_sample}"
            )

        with st.spinner("Writing…"):
            response = client.responses.create(
                model="gpt-4.1-mini",
                temperature=creativity,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"{instruction}\n\nTEXT:\n{user_text}"
                    }
                ],
            )

        st.text_area(
            "Result",
            value=response.output_text,
            height=400
        )
