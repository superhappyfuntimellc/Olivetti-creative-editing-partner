import streamlit as st
import re
from datetime import datetime
from openai import OpenAI

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Olivetti v12")
client = OpenAI()

# =========================
# SESSION STATE
# =========================
if "projects" not in st.session_state:
    st.session_state.projects = {}

if "current_project" not in st.session_state:
    st.session_state.current_project = None

if "current_chapter" not in st.session_state:
    st.session_state.current_chapter = 0

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

REVISION_MODES = {
    "Line Edit": "Improve clarity and flow. Do not add new content.",
    "Compress": "Cut redundancy. Reduce word count by ~15%.",
    "Sharpen Conflict": "Increase tension without changing events.",
    "Voice Consistency": "Align voice with the selected style."
}

# =========================
# HELPERS
# =========================
def normalize_chapter(ch):
    defaults = {
        "outline": "",
        "workflow": "Draft",
        "versions": [],
        "genre": "Literary",
        "voice": "Neutral Editor",
        "notes": "",
        "diagnostics": {}
    }
    for k, v in defaults.items():
        ch.setdefault(k, v)
    return ch

def split_into_chapters(text):
    parts = re.split(r"\n\s*(chapter\s+\d+|CHAPTER\s+\d+)\s*\n", text)
    chapters = []
    for i in range(1, len(parts), 2):
        chapters.append(normalize_chapter({
            "title": parts[i].title(),
            "text": parts[i+1].strip()
        }))
    if not chapters:
        chapters.append(normalize_chapter({
            "title": "Chapter 1",
            "text": text
        }))
    return chapters

def save_version(ch):
    ch["versions"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": ch["text"]
    })

def call_llm(system, prompt, temp=0.3):
    r = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        temperature=temp
    )
    return r.output_text

def generate_outline(ch):
    style = f"{GENRES[ch['genre']]} | {VOICES[ch['voice']]}"
    prompt = f"""
Create a concise chapter outline.
• Bullet points only
• Major story beats
• No rewriting

STYLE:
{style}

CHAPTER:
{ch['text']}
"""
    return call_llm("You are a professional developmental editor.", prompt)

def run_diagnostics(ch):
    prompt = f"""
Analyze this chapter. Do NOT rewrite.

Return:
• Scene purpose (1 sentence)
• What changes from start → end
• Pacing issues (if any)
• Redundant beats
• One concrete revision priority

CHAPTER:
{ch['text']}
"""
    return call_llm("You are a senior developmental editor.", prompt)

def revise_text(ch, mode):
    instruction = REVISION_MODES[mode]
    prompt = f"""
{instruction}

Maintain genre and voice.

GENRE: {ch['genre']}
VOICE: {ch['voice']}

TEXT:
{ch['text']}
"""
    return call_llm("You are a professional line editor.", prompt, temp=0.4)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("📁 Projects")
