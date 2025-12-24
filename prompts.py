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

def make_voice_learn_payload(sample_text: str) -> str:
    return f"""
TASK: Learn the author's writing voice from the sample.

{VOICE_LEARN_SCHEMA}

SAMPLE (author text):
{sample_text}
""".strip()
