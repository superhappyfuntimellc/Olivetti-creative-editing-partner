import streamlit as st
from datetime import datetime
from openai import OpenAI

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="🫒 Olivetti", layout="wide")
client = OpenAI()

# ============================================================
# SESSION STATE
# ============================================================
defaults = {
    "text": "",
    "focus": False,
    "last_saved": None,
    "voices": {},
    "active_voice": None,
    "junk": "",
    "synopsis": "",
    "genre_notes": "",
    "characters": "",
    "world": "",
    "outline": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================
# AUTOSAVE
# ============================================================
def autosave():
    st.session_state.last_saved = datetime.now().strftime("%H:%M:%S")

# ============================================================
# AI HELPERS
# ============================================================
def ai_ideas(section, text, temp=0.6):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
Generate useful creative ideas.
Do not explain. Do not label.

SECTION: {section}

CURRENT CONTENT:
{text}
""",
        temperature=temp
    )
    return text + "\n\n" + r.output_text

def ai_write(text):
    voice = None
    temp = 0.5

    if st.session_state.active_voice:
        voice = st.session_state.voices[st.session_state.active_voice]
        temp = 0.3 + voice["intensity"] * 0.6

    style = f"\nMatch this voice:\n{voice['sample']}\n" if voice else ""

    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "You are a professional novelist continuing prose."},
            {"role": "user", "content": f"{style}\nContinue the text naturally:\n{text}"}
        ],
        temperature=temp
    )
    return text + "\n\n" + r.output_text

# ============================================================
# TOP BAR
# ============================================================
t1, t2, t3, t4, t5 = st.columns([1,1,1,1,2])
t1.button("🆕 New")
t2.button("📝 Rough")
t3.button("✏️ First Edit")
t4.button("✅ Final")
if t5.button("🎯 Focus"):
    st.session_state.focus = not st.session_state.focus

st.divider()

# ============================================================
# LAYOUT (DEFINED ONCE)
# ============================================================
if st.session_state.focus:
    left = None
    center = st.container()
    right = None
else:
    left, center, right = st.columns([1.2, 3.6, 1.4])

# ============================================================
# LEFT — STORY BIBLE (CORRECT ORDER)
# ============================================================
if left:
    with left:
        st.subheader("📖 Story Bible")

        with st.expander("Junk Drawer", expanded=True):
            st.session_state.junk = st.text_area("", st.session_state.junk, height=100)
            if st.button("💡 Ideas", key="junk_ai"):
                st.session_state.junk = ai_ideas("Junk Drawer", st.session_state.junk)

        with st.expander("Synopsis"):
            st.session_state.synopsis = st.text_area("", st.session_state.synopsis, height=100)
            if st.button("💡 Ideas", key="syn_ai"):
                st.session_state.synopsis = ai_ideas("Synopsis", st.session_state.synopsis)

        with st.expander("Genre / Style"):
            st.session_state.genre_notes = st.text_area("", st.session_state.genre_notes, height=100)
            if st.button("💡 Ideas", key="genre_ai"):
                st.session_state.genre_notes = ai_ideas("Genre / Style", st.session_state.genre_notes, 0.5)

        with st.expander("Characters"):
            st.session_state.characters = st.text_area("", st.session_state.characters, height=140)
            if st.button("💡 Ideas", key="char_ai"):
                st.session_state.characters = ai_ideas("Characters", st.session_state.characters)

        with st.expander("World Elements"):
            st.session_state.world = st.text_area("", st.session_state.world, height=120)
            if st.button("💡 Ideas", key="world_ai"):
                st.session_state.world = ai_ideas("World Elements", st.session_state.world)

        with st.expander("Outline"):
            st.session_state.outline = st.text_area("", st.session_state.outline, height=180)
            if st.button("💡 Ideas", key="outline_ai"):
                st.session_state.outline = ai_ideas("Outline", st.session_state.outline)

# ============================================================
# CENTER — WRITING DESK (ALWAYS)
# ============================================================
with center:
    st.subheader("🫒 Writing Desk")

    st.session_state.text = st.text_area(
        "",
        st.session_state.text,
        height=420,
        placeholder="Type anytime. No project required.",
        on_change=autosave
    )

    if st.session_state.last_saved:
        st.caption(f"💾 Autosaved at {st.session_state.last_saved}")

    st.divider()

    a1,a2,a3,a4,a5 = st.columns(5)
    if a1.button("✍️ Write"):
        with st.spinner("Writing…"):
            st.session_state.text = ai_write(st.session_state.text)
            autosave()
    a2.button("🔁 Rewrite", disabled=True)
    a3.button("➕ Expand", disabled=True)
    a4.button("🔄 Rephrase", disabled=True)
    a5.button("🎨 Describe", disabled=True)

    b1,b2,b3,b4,b5 = st.columns(5)
    b1.button("🧹 Spell", disabled=True)
    b2.button("📐 Grammar", disabled=True)
    b3.button("🔍 Find", disabled=True)
    b4.button("📚 Synonym", disabled=True)
    b5.button("🧠 Sentence", disabled=True)

# ============================================================
# RIGHT — VOICE BIBLE (FIXED)
# ============================================================
if right:
    with right:
        st.subheader("🎭 Voice Bible")

        names = ["— Neutral —"] + list(st.session_state.voices.keys())
        choice = st.selectbox("Active Voice", names)
        st.session_state.active_voice = None if choice == "— Neutral —" else choice

        intensity = st.slider("Intensity", 0.0, 1.0, 0.5)

        with st.expander("Train New Voice"):
            vname = st.text_input("Voice Name")
            vsample = st.text_area("Training Sample", height=120)
            if st.button("Save Voice"):
                if vname and vsample:
                    st.session_state.voices[vname] = {
                        "sample": vsample,
                        "intensity": intensity
                    }
                    st.session_state.active_voice = vname

# ============================================================
# FOOTER
# ============================================================
st.caption("Olivetti — stable authorial desk")
