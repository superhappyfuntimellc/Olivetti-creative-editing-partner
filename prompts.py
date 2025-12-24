VOICE_LEARN_SCHEMA = """
Return STRICT JSON only (no markdown, no commentary) with keys:
style_notes: string
pov: string
tense: string
sentence_rhythm: string
imagery_profile: string
dialogue_profile: string
do: array of short strings
dont: array of short strings
lexicon: array of favored words/phrases (max 30)
anti_lexicon: array of words/phrases to avoid (max 30)
metaphor_policy: string
profanity_policy: string
"""
build_instructions()
pov = vb.get("pov", "")
tense = vb.get("tense", "")
rhythm = vb.get("sentence_rhythm", "")
imagery = vb.get("imagery_profile", "")
dialogue = vb.get("dialogue_profile", "")
anti = vb.get("anti_lexicon", [])

return f"""
...
Voice Bible:
- POV: {pov}
- Tense: {tense}
- Sentence rhythm: {rhythm}
- Imagery: {imagery}
- Dialogue: {dialogue}
- Style notes: {style}
- Do: {do}
- Don't: {dont}
- Lexicon: {lex}
- Avoid: {anti}
""".strip()

def make_voice_learn_payload(sample_text: str) -> str:
    return f"""
TASK: Learn the author's writing voice from the sample.

{VOICE_LEARN_SCHEMA}

SAMPLE (author text):
{sample_text}
""".strip()
