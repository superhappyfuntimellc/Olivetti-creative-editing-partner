# --- ADD TO YOUR EXISTING IMPORTS ---
import difflib

# ============================================================
# FUN / CREATIVE HELPERS
# ============================================================
def comment_on_text(text, intensity):
    prompt = f"""
You are a sharp but respectful literary editor.

Give margin comments ONLY.
No rewriting.
No summaries.

Intensity level: {intensity}/10

Flag:
- Flat language
- Voice drift
- Overwriting
- Missed opportunities

TEXT:
{text}
"""
    return llm("You are a senior fiction editor.", prompt, 0.4)

def synonym_suggestions(word, intensity):
    prompt = f"""
Give synonym suggestions for the word: "{word}"

Return sections:
SOFTER
SHARPER
STRANGER

Intensity: {intensity}/10
"""
    return llm("You are a master stylist.", prompt, 0.4)

def preview_find_replace(text, find, replace):
    return list(difflib.ndiff(text.split(), text.replace(find, replace).split()))

# ============================================================
# RIGHT COLUMN — FUN TOOLS
# ============================================================
with right:
    st.subheader("🎛 Creative Tools")

    intensity = st.slider(
        "Intensity",
        0.0, 10.0, 5.0, 0.5,
        help="Controls how bold AI suggestions are"
    )

    st.divider()
    st.subheader("💬 Margin Notes")

    if st.button("Analyze Chapter (Comments Only)"):
        with st.spinner("Annotating…"):
            ch["notes"] = comment_on_text(ch["text"], intensity)

    if ch.get("notes"):
        st.text_area("Editor Notes", ch["notes"], height=200)

    st.divider()
    st.subheader("🧠 Synonym Playground")

    target_word = st.text_input("Word to explore")
    if st.button("Suggest Alternatives") and target_word:
        with st.spinner("Thinking…"):
            ch["synonyms"] = synonym_suggestions(target_word, intensity)

    if ch.get("synonyms"):
        st.text_area("Suggestions", ch["synonyms"], height=180)

    st.divider()
    st.subheader("🔍 Find & Replace++")

    find = st.text_input("Find")
    replace = st.text_input("Replace with")

    if st.button("Preview Replace") and find:
        preview = preview_find_replace(ch["text"], find, replace)
        st.text_area("Preview (diff)", "\n".join(preview[:400]), height=200)

    if st.button("Apply Replace") and find:
        ch["text"] = ch["text"].replace(find, replace)
        st.success("Replacement applied.")
