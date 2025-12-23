import streamlit as st
import re
from datetime import datetime
from openai import OpenAI
from difflib import get_close_matches

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="🫒 Olivetti 19.6")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
for key, default in {
    "projects": {},
    "current_project": None,
    "current_chapter": 0,
    "voice_strictness": 0.4,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# =========================
# STYLE PRESETS
# =========================
GENRES = {
    "Literary": "Elegant prose, interiority, subtle metaphor.",
    "Noir": "Hard-edged, cynical, concrete imagery.",
    "Thriller": "Fast pacing, tension, urgency.",
    "Comedy": "Timing, irony, wit, lightness.",
    "Lyrical": "Rhythm, imagery, musical language.",
    "Ironic": "Detached, sharp, understated humor."
}

VOICES = {
    "Neutral Editor": "Clear, professional, invisible style.",
    "Minimal": "Short sentences. Subtext. Restraint.",
    "Expressive": "Emotion-forward, dynamic voice.",
    "Hardboiled": "Dry, blunt, unsentimental.",
    "Poetic": "Figurative, flowing, evocative."
}

# =========================
# HELPERS
# =========================
def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append({
