import os
import re
import math
import json
import hashlib
from io import BytesIO
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

import streamlit as st

# ============================================================
# OLIVETTI DESK — one file, production-stable, paste+click
# ============================================================

# ============================================================
# ENV / METADATA HYGIENE
# ============================================================
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

DEFAULT_MODEL = "gpt-4.1-mini"
try:
    OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)  # type: ignore[attr-defined]
except Exception:
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

def _get_openai_key_or_empty() -> str:
    """Return key if present (secrets/env), else '' (no UI side effects)."""
    try:
        key = (st.secrets.get("OPENAI_API_KEY", "") or "").strip()  # type: ignore[attr-defined]
    except Exception:
        key = ""
    if not key:
        key = (os.getenv("OPENAI_API_KEY", "") or "").strip()
    return key

# Cached (non-fatal) key presence for UI gating; use require_openai_key() before any API call.
OPENAI_API_KEY = _get_openai_key_or_empty()


def require_openai_key() -> str:
    """Stop the app with a user-facing message if OPENAI_API_KEY is missing."""
    key = _get_openai_key_or_empty()
    if not key:
        st.error(
            """Missing **OPENAI_API_KEY**.

Add it in Streamlit Cloud → App → Settings → Secrets, or set it as an environment variable.

Example Secrets:
OPENAI_API_KEY = "sk-..."
"""
        )
        st.stop()
    return key

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti Desk", layout="wide", initial_sidebar_state="expanded")

# Sexy, readable UI skin — no feature changes
st.markdown(
    """
<style>
:root{
  --bg0:#07090d;
  --bg1:#0b0f16;
  --panel:rgba(17,21,28,.82);
  --panel2:rgba(22,28,38,.78);
  --stroke:rgba(202,168,106,.22);
  --stroke2:rgba(255,255,255,.08);
  --accent:#caa86a;
  --text:#e9edf5;
  --muted:rgba(233,237,245,.72);
  --paper:#fbf7ee;
  --ink:#14161a;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"]{
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
}
h1, h2, h3, h4, h5, .stSubheader{
  font-family: ui-serif, Georgia, "Palatino Linotype", Palatino, serif;
}

.stApp{
  background:
    radial-gradient(1200px 800px at 20% 0%, rgba(109,214,255,.10), transparent 60%),
    radial-gradient(900px 700px at 90% 10%, rgba(202,168,106,.12), transparent 55%),
    linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 100%);
  color: var(--text);
}

header[data-testid="stHeader"]{ background: transparent; }

[data-testid="stSidebar"]{
  background: linear-gradient(180deg, rgba(13,16,23,.92), rgba(10,12,18,.86));
  border-right: 1px solid var(--stroke);
  box-shadow: 0 0 0 1px rgba(255,255,255,.03) inset, 10px 0 40px rgba(0,0,0,.35);
}
[data-testid="stSidebar"] *{ color: var(--text); }

section.main > div.block-container{
  padding-top: 1.25rem;
  padding-bottom: 2rem;
  max-width: 1500px;
}

details[data-testid="stExpander"]{
  background: var(--panel);
  border: 1px solid var(--stroke2);
  border-radius: 16px;
  box-shadow: 0 0 0 1px rgba(0,0,0,.25) inset, 0 12px 30px rgba(0,0,0,.28);
  overflow: hidden;
}
details[data-testid="stExpander"] > summary{
  padding: 0.65rem 0.9rem !important;
  font-size: 0.95rem !important;
  letter-spacing: .2px;
  color: var(--text);
  background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(0,0,0,0));
  border-bottom: 1px solid rgba(255,255,255,.06);
}
details[data-testid="stExpander"][open] > summary{ border-bottom: 1px solid rgba(202,168,106,.16); }

div[data-testid="stTextArea"] textarea{
  font-size: 18px !important;
  line-height: 1.65 !important;
  padding: 18px !important;
  resize: vertical !important;
  min-height: 520px !important;
  background: var(--paper) !important;
  color: var(--ink) !important;
  border: 1px solid rgba(20,22,26,.18) !important;
  box-shadow: 0 1px 0 rgba(255,255,255,.55) inset, 0 10px 24px rgba(0,0,0,.18) !important;
}
div[data-testid="stTextArea"] textarea:focus{
  outline: none !important;
  border: 1px solid rgba(202,168,106,.55) !important;
  box-shadow: 0 0 0 3px rgba(202,168,106,.18), 0 10px 24px rgba(0,0,0,.20) !important;
}

button[kind="secondary"], button[kind="primary"]{
  font-size: 16px !important;
  padding: 0.62rem 0.95rem !important;
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,.10) !important;
  transition: transform .08s ease, box-shadow .12s ease, border-color .12s ease, filter .12s ease;
}
button[kind="primary"]{
  background: linear-gradient(180deg, rgba(202,168,106,.95), rgba(150,118,64,.92)) !important;
  color: #161616 !important;
  box-shadow: 0 10px 24px rgba(0,0,0,.28), 0 0 0 1px rgba(0,0,0,.22) inset !important;
}
button[kind="secondary"]{
  background: linear-gradient(180deg, rgba(255,255,255,.06), rgba(255,255,255,.02)) !important;
  color: var(--text) !important;
  box-shadow: 0 8px 18px rgba(0,0,0,.22), 0 0 0 1px rgba(0,0,0,.25) inset !important;
}
button:hover{
  transform: translateY(-1px);
  border-color: rgba(202,168,106,.35) !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.30), 0 0 0 1px rgba(202,168,106,.20) inset !important;
  filter: brightness(1.03);
}

[data-testid="stTabs"] [data-baseweb="tab-list"]{ gap: 8px; }
[data-testid="stTabs"] button[role="tab"]{
  border-radius: 999px !important;
  padding: 0.35rem 0.8rem !important;
  background: rgba(255,255,255,.04) !important;
  border: 1px solid rgba(255,255,255,.08) !important;
  color: var(--text) !important;
}
[data-testid="stTabs"] button[aria-selected="true"]{
  background: rgba(202,168,106,.18) !important;
  border-color: rgba(202,168,106,.28) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# GLOBALS
# ============================================================
LANES = ["Dialogue", "Narration", "Interiority", "Action"]
BAYS = ["NEW", "ROUGH", "EDIT", "FINAL"]


ENGINE_STYLES = ["NARRATIVE", "DESCRIPTIVE", "EMOTIONAL", "LYRICAL"]
AUTOSAVE_DIR = "autosave"
AUTOSAVE_PATH = os.path.join(AUTOSAVE_DIR, "olivetti_state.json")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB guardrail

WORD_RE = re.compile(r"[A-Za-z']+")


# ============================================================
# UTILS
# ============================================================
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _normalize_text(s: str) -> str:
    t = (s or "").strip()
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def _split_paragraphs(text: str) -> List[str]:
    t = _normalize_text(text)
    if not t:
        return []
    return [p.strip() for p in re.split(r"\n\s*\n", t, flags=re.MULTILINE) if p.strip()]


def _safe_filename(s: str, fallback: str = "olivetti") -> str:
    s = re.sub(r"[^\w\- ]+", "", (s or "").strip()).strip()
    s = re.sub(r"\s+", "_", s)
    return s[:80] if s else fallback


def _clamp_text(s: str, max_chars: int = 12000) -> str:
    s = s or ""
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 40] + "\n\n… (truncated) …"


# ============================================================
# VECTOR / VOICE VAULT (lightweight, no external deps)
# ============================================================
def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in WORD_RE.findall(text or "")]


def _hash_vec(text: str, dims: int = 512) -> List[float]:
    vec = [0.0] * dims
    toks = _tokenize(text)
    for t in toks:
        h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
        vec[h % dims] += 1.0
    for i, v in enumerate(vec):
        if v > 0:
            vec[i] = 1.0 + math.log(v)
    return vec


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def default_voice_vault() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "Voice A": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
        "Voice B": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
    }


def rebuild_vectors_in_voice_vault(compact_voices: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for vname, v in (compact_voices or {}).items():
        created_ts = v.get("created_ts") or now_ts()
        lanes_in = v.get("lanes", {}) or {}
        lanes_out: Dict[str, Any] = {ln: [] for ln in LANES}
        for ln in LANES:
            samples = lanes_in.get(ln, []) or []
            for s in samples:
                txt = _normalize_text(s.get("text", ""))
                if not txt:
                    continue
                lanes_out[ln].append({
                    "ts": s.get("ts") or now_ts(),
                    "text": txt,
                    "vec": _hash_vec(txt),
                })
        out[vname] = {"created_ts": created_ts, "lanes": lanes_out}
    return out


def compact_voice_vault(voices: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for vname, v in (voices or {}).items():
        lanes_out: Dict[str, Any] = {}
        for ln in LANES:
            samples = (v.get("lanes", {}) or {}).get(ln, []) or []
            lanes_out[ln] = [
                {"ts": s.get("ts"), "text": s.get("text", "")}
                for s in samples
                if (s.get("text") or "").strip()
            ]
        out[vname] = {"created_ts": v.get("created_ts"), "lanes": lanes_out}
    return out


def voice_names_for_selector() -> List[str]:
    base = ["— None —", "Voice A", "Voice B"]
    customs = sorted([k for k in (st.session_state.voices or {}).keys() if k not in ("Voice A", "Voice B")])
    return base + customs


def create_custom_voice(name: str) -> bool:
    n = (name or "").strip()
    if not n:
        return False
    if n in (st.session_state.voices or {}):
        return False
    st.session_state.voices[n] = {"created_ts": now_ts(), "lanes": {ln: [] for ln in LANES}}
    return True


def add_voice_sample(voice_name: str, lane: str, text: str) -> bool:
    vn = (voice_name or "").strip()
    if not vn:
        return False
    lane = lane if lane in LANES else "Narration"
    t = _normalize_text(text)
    if not t:
        return False
    v = (st.session_state.voices or {}).get(vn)
    if not v:
        # auto-create
        create_custom_voice(vn)
        v = st.session_state.voices.get(vn)
    v.setdefault("lanes", {ln: [] for ln in LANES})
    v["lanes"].setdefault(lane, [])
    v["lanes"][lane].append({"ts": now_ts(), "text": t, "vec": _hash_vec(t)})
    # cap per lane (keeps app fast)
    if len(v["lanes"][lane]) > 60:
        v["lanes"][lane] = v["lanes"][lane][-60:]
    st.session_state.voices[vn] = v
    return True


def delete_voice_sample(voice_name: str, lane: str, index_from_end: int = 0) -> bool:
    vn = (voice_name or "").strip()
    v = (st.session_state.voices or {}).get(vn)
    if not v:
        return False
    lane = lane if lane in LANES else "Narration"
    arr = (v.get("lanes", {}) or {}).get(lane, []) or []
    if not arr:
        return False
    idx = len(arr) - 1 - int(index_from_end)
    if idx < 0 or idx >= len(arr):
        return False
    arr.pop(idx)
    v["lanes"][lane] = arr
    st.session_state.voices[vn] = v
    return True


def retrieve_exemplars(voice_name: str, lane: str, query_text: str, k: int = 3) -> List[str]:
    v = (st.session_state.voices or {}).get(voice_name)
    if not v:
        return []
    lane = lane if lane in LANES else "Narration"
    pool = v.get("lanes", {}).get(lane, []) or []
    if not pool:
        return []
    qv = _hash_vec(query_text)
    scored = [(_cosine(qv, s.get("vec", [])), s.get("text", "")) for s in pool[-140:]]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [txt for score, txt in scored[:k] if score > 0.0 and txt][:k]


def retrieve_mixed_exemplars(voice_name: str, lane: str, query_text: str) -> List[str]:
    lane_ex = retrieve_exemplars(voice_name, lane, query_text, k=2)
    if lane == "Narration":
        return lane_ex if lane_ex else retrieve_exemplars(voice_name, "Narration", query_text, k=3)
    nar_ex = retrieve_exemplars(voice_name, "Narration", query_text, k=1)
    out = lane_ex + [x for x in nar_ex if x not in lane_ex]
    return out[:3]


# ============================================================
# LANE DETECTION (lightweight)
# ============================================================
THOUGHT_WORDS = {
    "think",
    "thought",
    "felt",
    "wondered",
    "realized",
    "remembered",
    "knew",
    "noticed",
    "decided",
    "hoped",
    "feared",
    "wanted",
    "imagined",
    "could",
    "should",
    "would",
}
ACTION_VERBS = {
    "run",
    "ran",
    "walk",
    "walked",
    "grab",
    "grabbed",
    "push",
    "pushed",
    "pull",
    "pulled",
    "slam",
    "slammed",
    "hit",
    "struck",
    "kick",
    "kicked",
    "turn",
    "turned",
    "snap",
    "snapped",
    "dive",
    "dived",
    "duck",
    "ducked",
    "rush",
    "rushed",
    "lunge",
    "lunged",
    "climb",
    "climbed",
    "drop",
    "dropped",
    "throw",
    "threw",
    "fire",
    "fired",
    "aim",
    "aimed",
    "break",
    "broke",
    "shatter",
    "shattered",
    "step",
    "stepped",
    "move",
    "moved",
    "reach",
    "reached",
}


def detect_lane(paragraph: str) -> str:
    p = (paragraph or "").strip()
    if not p:
        return "Narration"

    quote_count = p.count('"') + p.count("“") + p.count("”")
    has_dialogue_punct = p.startswith(("—", "- ", "“", '"'))

    dialogue_score = 0.0
    if quote_count >= 2:
        dialogue_score += 2.5
    if has_dialogue_punct:
        dialogue_score += 1.5

    toks = _tokenize(p)
    interior_score = 0.0
    if toks:
        first_person = sum(1 for t in toks if t in ("i", "me", "my", "mine", "myself"))
        thought_hits = sum(1 for t in toks if t in THOUGHT_WORDS)
        if first_person >= 2 and thought_hits >= 1:
            interior_score += 2.2

    action_score = 0.0
    if toks:
        verb_hits = sum(1 for t in toks if t in ACTION_VERBS)
        if verb_hits >= 2:
            action_score += 1.6
        if "!" in p:
            action_score += 0.3

    scores = {"Dialogue": dialogue_score, "Interiority": interior_score, "Action": action_score, "Narration": 0.25}
    lane = max(scores.items(), key=lambda kv: kv[1])[0]
    return "Narration" if scores[lane] < 0.9 else lane


def current_lane_from_draft(text: str) -> str:
    paras = _split_paragraphs(text)
    if not paras:
        return "Narration"
    return detect_lane(paras[-1])


# ============================================================
# INTENSITY (GLOBAL AI AGGRESSION KNOB)
# ============================================================
def intensity_profile(x: float) -> str:
    if x <= 0.25:
        return "LOW: conservative, literal, minimal invention, prioritize continuity and clarity."
    if x <= 0.60:
        return "MED: balanced creativity, stronger phrasing, controlled invention within canon."
    if x <= 0.85:
        return "HIGH: bolder choices, richer specificity; still obey canon and lane."
    return "MAX: aggressive originality and voice; still obey canon, no derailments."


def temperature_from_intensity(x: float) -> float:
    x = max(0.0, min(1.0, float(x)))
    return 0.15 + (x * 0.95)


# ============================================================
# PROJECT MODEL
# ============================================================
def _fingerprint_story_bible(sb: Dict[str, str]) -> str:
    parts = [
        (sb.get("synopsis", "") or "").strip(),
        (sb.get("genre_style_notes", "") or "").strip(),
        (sb.get("world", "") or "").strip(),
        (sb.get("characters", "") or "").strip(),
        (sb.get("outline", "") or "").strip(),
    ]
    blob = "\n\n---\n\n".join(parts)
    return hashlib.md5(blob.encode("utf-8")).hexdigest()


def new_project_payload(title: str) -> Dict[str, Any]:
    ts = now_ts()
    title = title.strip() if title.strip() else "Untitled Project"
    story_bible_id = hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": hashlib.md5(f"{title}|{ts}".encode("utf-8")).hexdigest()[:12],
        "title": title,
        "created_ts": ts,
        "updated_ts": ts,
        "bay": "NEW",
        "draft": "",
        "story_bible_id": story_bible_id,
        "story_bible_created_ts": ts,
        "story_bible_binding": {"locked": True, "locked_ts": ts, "source": "system", "source_story_bible_id": None},
        "story_bible_fingerprint": "",
        "story_bible": {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""},
        "voice_bible": {
            "vb_style_on": True,
            "vb_genre_on": True,
            "vb_trained_on": False,
            "vb_match_on": False,
            "vb_lock_on": False,
            "writing_style": "Neutral",
            "genre": "Literary",
            "trained_voice": "— None —",
            "voice_sample": "",
            "voice_lock_prompt": "",
            "style_intensity": 0.6,
            "genre_intensity": 0.6,
            "trained_intensity": 0.7,
            "match_intensity": 0.8,
            "lock_intensity": 1.0,
            "pov": "Close Third",
            "tense": "Past",
            "ai_intensity": 0.75,
        },
        "locks": {
            "story_bible_lock": True,  # relationship lock
            "sb_edit_unlocked": False,  # hard lock for edits (content)
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },
        "voices": default_voice_vault(),
        "style_banks": default_style_banks(),
    }


# ============================================================

# ============================================================
# ENGINE STYLE BANKS (project/workspace) — trainable writing styles
# ============================================================
def default_style_banks() -> Dict[str, Any]:
    ts = now_ts()
    return {s: {"created_ts": ts, "lanes": {ln: [] for ln in LANES}} for s in ENGINE_STYLES}


def rebuild_vectors_in_style_banks(banks: Dict[str, Any]) -> Dict[str, Any]:
    src = banks or {}
    out: Dict[str, Any] = {}
    for style in ENGINE_STYLES:
        b = (src.get(style) or {}) if isinstance(src, dict) else {}
        lanes = b.get("lanes") or {}
        new_lanes: Dict[str, List[Dict[str, Any]]] = {}
        for ln in LANES:
            samples = (lanes.get(ln) or []) if isinstance(lanes, dict) else []
            rebuilt: List[Dict[str, Any]] = []
            for it in samples:
                if isinstance(it, str):
                    t = it.strip()
                    if not t:
                        continue
                    rebuilt.append({"ts": now_ts(), "text": t, "vec": _hash_vec(t)})
                    continue
                if not isinstance(it, dict):
                    continue
                t = (it.get("text") or "").strip()
                if not t:
                    continue
                vec = it.get("vec") if isinstance(it.get("vec"), list) else None
                if not vec:
                    vec = _hash_vec(t)
                rebuilt.append({"ts": it.get("ts") or now_ts(), "text": t, "vec": vec})
            new_lanes[ln] = rebuilt
        out[style] = {"created_ts": b.get("created_ts") or now_ts(), "lanes": new_lanes}
    return out if out else default_style_banks()


def compact_style_banks(banks: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(banks, dict):
        return default_style_banks()
    out: Dict[str, Any] = {}
    for style in ENGINE_STYLES:
        b = banks.get(style) or {}
        lanes = b.get("lanes") or {}
        c_lanes: Dict[str, List[Dict[str, Any]]] = {}
        for ln in LANES:
            ss = (lanes.get(ln) or []) if isinstance(lanes, dict) else []
            cleaned: List[Dict[str, Any]] = []
            for it in ss:
                if not isinstance(it, dict):
                    continue
                t = (it.get("text") or "").strip()
                if not t:
                    continue
                cleaned.append({"ts": it.get("ts") or now_ts(), "text": _clamp_text(t, 9000)})
            c_lanes[ln] = cleaned
        out[style] = {"created_ts": b.get("created_ts") or now_ts(), "lanes": c_lanes}
    return out


def add_style_samples(style: str, lane: str, raw_text: str, split_mode: str = "Paragraphs", cap_per_lane: int = 250) -> int:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return 0
    lane = lane if lane in LANES else "Narration"
    t = _normalize_text(raw_text)
    if not t.strip():
        return 0

    parts = _split_paragraphs(t) if split_mode == "Paragraphs" else [t.strip()]
    parts = [p for p in parts if len(p.strip()) >= 40]

    sb = st.session_state.get("style_banks")
    if not isinstance(sb, dict) or style not in sb:
        sb = rebuild_vectors_in_style_banks(default_style_banks())
        st.session_state.style_banks = sb

    bank = sb.get(style) or {}
    lanes = bank.get("lanes") or {}
    lane_list = list((lanes.get(lane) or [])) if isinstance(lanes, dict) else []

    added = 0
    for p in parts:
        p = _clamp_text(p.strip(), 9000)
        lane_list.append({"ts": now_ts(), "text": p, "vec": _hash_vec(p)})
        added += 1

    # cap: keep newest
    lane_list = lane_list[-cap_per_lane:]
    lanes[lane] = lane_list
    bank["lanes"] = lanes
    sb[style] = bank
    st.session_state.style_banks = sb
    return added


def delete_last_style_sample(style: str, lane: str) -> bool:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return False
    lane = lane if lane in LANES else "Narration"
    sb = st.session_state.get("style_banks") or {}
    bank = (sb.get(style) or {})
    lanes = bank.get("lanes") or {}
    lane_list = (lanes.get(lane) or [])
    if not lane_list:
        return False
    lane_list.pop()
    lanes[lane] = lane_list
    bank["lanes"] = lanes
    sb[style] = bank
    st.session_state.style_banks = sb
    return True


def clear_style_lane(style: str, lane: str) -> None:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return
    lane = lane if lane in LANES else "Narration"
    sb = st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks())
    bank = sb.get(style) or {}
    lanes = bank.get("lanes") or {}
    lanes[lane] = []
    bank["lanes"] = lanes
    sb[style] = bank
    st.session_state.style_banks = sb


def retrieve_style_exemplars(style: str, lane: str, query: str, k: int = 2) -> List[str]:
    style = (style or "").strip().upper()
    if style not in ENGINE_STYLES:
        return []
    lane = lane if lane in LANES else "Narration"
    sb = st.session_state.get("style_banks") or {}
    bank = sb.get(style) or {}
    lanes = bank.get("lanes") or {}
    pool = (lanes.get(lane) or [])
    if not pool:
        # fallback: all lanes pooled
        pool = []
        for ln in LANES:
            pool.extend(lanes.get(ln) or [])
    if not pool:
        return []
    # favor newest slice for speed
    pool = pool[-160:]
    qv = _hash_vec(query or "")
    scored = []
    for it in pool:
        if not isinstance(it, dict):
            continue
        vec = it.get("vec")
        if not isinstance(vec, list):
            continue
        scored.append((_cosine(qv, vec), it.get("text") or ""))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = [t.strip() for _, t in scored[: max(0, k)] if (t or "").strip()]
    return out


_ENGINE_STYLE_GUIDE = {
    "NARRATIVE": "Narrative clarity, clean cause→effect, confident pacing. Prioritize story logic and readability.",
    "DESCRIPTIVE": "Sensory precision, spatial clarity, vivid concrete nouns, controlled detail density (no purple bloat).",
    "EMOTIONAL": "Interior depth, subtext, emotional specificity. Show the feeling through behavior, sensation, and thought.",
    "LYRICAL": "Rhythm, musical syntax, image-forward language, elegant metaphor with restraint. Make prose sing without obscuring meaning.",
}


def engine_style_directive(style: str, intensity: float, lane: str) -> str:
    style = (style or "").strip().upper()
    base = _ENGINE_STYLE_GUIDE.get(style, "")
    x = float(intensity)
    if x <= 0.33:
        mod = "Keep it subtle and controlled. Minimal overt stylization."
    elif x <= 0.66:
        mod = "Medium stylization. Let the style clearly shape diction and cadence."
    else:
        mod = "High stylization. Strong stylistic fingerprint, but still professional and coherent."
    return f"{base}\\nLane: {lane}\\n{mod}"


# STORY BIBLE WORKSPACE (pre-project creation space)
# ============================================================
def default_story_bible_workspace() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "workspace_story_bible_id": hashlib.md5(f"wsb|{ts}".encode("utf-8")).hexdigest()[:12],
        "workspace_story_bible_created_ts": ts,
        "title": "",
        "draft": "",
        "story_bible": {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""},
        "voice_sample": "",
        "ai_intensity": 0.75,
        "voices": default_voice_vault(),
        "style_banks": default_style_banks(),
    }


def in_workspace_mode() -> bool:
    return (st.session_state.active_bay == "NEW") and (st.session_state.project_id is None)


def save_workspace_from_session() -> None:
    w = st.session_state.sb_workspace or default_story_bible_workspace()
    w["title"] = st.session_state.get("workspace_title", w.get("title", ""))
    w["draft"] = st.session_state.main_text
    w["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }
    w["voice_sample"] = st.session_state.voice_sample
    w["ai_intensity"] = float(st.session_state.ai_intensity)
    w["voices"] = compact_voice_vault(st.session_state.voices)
    w["style_banks"] = compact_style_banks(st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks()))
    st.session_state.sb_workspace = w


def load_workspace_into_session() -> None:
    w = st.session_state.sb_workspace or default_story_bible_workspace()
    sb = w.get("story_bible", {}) or {}
    st.session_state.project_id = None
    st.session_state.project_title = "—"
    st.session_state.main_text = w.get("draft", "") or ""
    st.session_state.synopsis = sb.get("synopsis", "") or ""
    st.session_state.genre_style_notes = sb.get("genre_style_notes", "") or ""
    st.session_state.world = sb.get("world", "") or ""
    st.session_state.characters = sb.get("characters", "") or ""
    st.session_state.outline = sb.get("outline", "") or ""
    st.session_state.voice_sample = w.get("voice_sample", "") or ""
   
    st.session_state.voices = rebuild_vectors_in_voice_vault(w.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True
    st.session_state.style_banks = rebuild_vectors_in_style_banks(w.get("style_banks", default_style_banks()))
    st.session_state.workspace_title = w.get("title", "") or ""
if "ai_intensity" not in st.session_state:
    st.session_state.ai_intensity = float(w.get("ai_intensity", 0.75))
else:
    st.session_state["ai_intensity_pending"] = float(w.get("ai_intensity", 0.75))
    st.session_state["_apply_pending_widget_state"] = True

def reset_workspace_story_bible(keep_templates: bool = True) -> None:
    old = st.session_state.sb_workspace or default_story_bible_workspace()
    neww = default_story_bible_workspace()
    if keep_templates:
        neww["voice_sample"] = old.get("voice_sample", "")
        neww["ai_intensity"] = float(old.get("ai_intensity", 0.75))
        neww["voices"] = old.get("voices", default_voice_vault())
        neww["style_banks"] = old.get("style_banks", default_style_banks())
    st.session_state.sb_workspace = neww
    if in_workspace_mode():
        load_workspace_into_session()


# ============================================================
# SESSION INIT
# ============================================================
def init_state() -> None:
    defaults: Dict[str, Any] = {
        "ai_intensity": 0.75,
        "active_bay": "NEW",
        "projects": {},
        "active_project_by_bay": {b: None for b in BAYS},
        "sb_workspace": default_story_bible_workspace(),
        "workspace_title": "",
        "project_id": None,
        "project_title": "—",
        "autosave_time": None,
        "last_action": "—",
        "voice_status": "—",
        "main_text": "",
        "synopsis": "",
        "genre_style_notes": "",
        "world": "",
        "characters": "",
        "outline": "",
        "junk": "",
        "tool_output": "",
        "pending_action": None,
        "vb_style_on": True,
        "vb_genre_on": True,
        "vb_trained_on": False,
        "vb_match_on": False,
        "vb_lock_on": False,
        "writing_style": "Neutral",
        "genre": "Literary",
        "trained_voice": "— None —",
        "voice_sample": "",
        "voice_lock_prompt": "",
        "style_intensity": 0.6,
        "genre_intensity": 0.6,
        "trained_intensity": 0.7,
        "match_intensity": 0.8,
        "lock_intensity": 1.0,
        "pov": "Close Third",
        "tense": "Past",
        "ai_intensity": 0.75,
        "locks": {
            "story_bible_lock": True,
            "sb_edit_unlocked": False,
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },
        "voices": {},
        "voices_seeded": False,
        "style_banks": rebuild_vectors_in_style_banks(default_style_banks()),
        "last_saved_digest": "",

        # internal UI helpers (not widgets)
        "ui_notice": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()
# Apply pending widget values BEFORE widgets are created
if st.session_state.pop("_apply_pending_widget_state", False):
    if "ai_intensity_pending" in st.session_state:
    st.session_state["ai_intensity"] = float(st.session_state.pop("ai_intensity_pending"))
   


# ============================================================
# PROJECT <-> SESSION SYNC
# ============================================================
def load_project_into_session(pid: str) -> None:
    p = (st.session_state.projects or {}).get(pid)
    if not p:
        return

    st.session_state.project_id = pid
    st.session_state.project_title = p.get("title", "Untitled Project")
    st.session_state.main_text = p.get("draft", "")

    sb = p.get("story_bible", {}) or {}
    st.session_state.synopsis = sb.get("synopsis", "")
    st.session_state.genre_style_notes = sb.get("genre_style_notes", "")
    st.session_state.world = sb.get("world", "")
    st.session_state.characters = sb.get("characters", "")
    st.session_state.outline = sb.get("outline", "")

    vb = p.get("voice_bible", {}) or {}
    for k in [
        "vb_style_on",
        "vb_genre_on",
        "vb_trained_on",
        "vb_match_on",
        "vb_lock_on",
        "writing_style",
        "genre",
        "trained_voice",
        "voice_sample",
        "voice_lock_prompt",
        "style_intensity",
        "genre_intensity",
        "trained_intensity",
        "match_intensity",
        "lock_intensity",
        "pov",
        "tense",
        "ai_intensity",
    ]:
        if k in vb:
            st.session_state[k] = vb[k]

    locks = p.get("locks", {}) or {}
    if isinstance(locks, dict):
        # ensure new keys exist
        locks.setdefault("sb_edit_unlocked", False)
        st.session_state.locks = locks

    st.session_state.voices = rebuild_vectors_in_voice_vault(p.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True


def save_session_into_project() -> None:
    pid = st.session_state.project_id
    if not pid:
        return
    p = (st.session_state.projects or {}).get(pid)
    if not p:
        return

    p["updated_ts"] = now_ts()
    p["draft"] = st.session_state.main_text
    p["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }
    p["voice_bible"] = {
        "vb_style_on": st.session_state.vb_style_on,
        "vb_genre_on": st.session_state.vb_genre_on,
        "vb_trained_on": st.session_state.vb_trained_on,
        "vb_match_on": st.session_state.vb_match_on,
        "vb_lock_on": st.session_state.vb_lock_on,
        "writing_style": st.session_state.writing_style,
        "genre": st.session_state.genre,
        "trained_voice": st.session_state.trained_voice,
        "voice_sample": st.session_state.voice_sample,
        "voice_lock_prompt": st.session_state.voice_lock_prompt,
        "style_intensity": st.session_state.style_intensity,
        "genre_intensity": st.session_state.genre_intensity,
        "trained_intensity": st.session_state.trained_intensity,
        "match_intensity": st.session_state.match_intensity,
        "lock_intensity": st.session_state.lock_intensity,
        "pov": st.session_state.pov,
        "tense": st.session_state.tense,
        "ai_intensity": float(st.session_state.ai_intensity),
    }
    p["locks"] = st.session_state.locks
    p["voices"] = compact_voice_vault(st.session_state.voices)
    p["style_banks"] = compact_style_banks(st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks()))
    # keep fingerprint up to date
    try:
        p["story_bible_fingerprint"] = _fingerprint_story_bible(p["story_bible"])
    except Exception:
        pass


def list_projects_in_bay(bay: str) -> List[Tuple[str, str]]:
    items: List[Tuple[str, str]] = []
    for pid, p in (st.session_state.projects or {}).items():
        if isinstance(p, dict) and p.get("bay") == bay:
            items.append((pid, p.get("title", "Untitled")))
    items.sort(key=lambda x: (x[1] or "").lower())
    return items


def ensure_bay_has_active_project(bay: str) -> None:
    pid = (st.session_state.active_project_by_bay or {}).get(bay)
    if pid and pid in (st.session_state.projects or {}) and (st.session_state.projects[pid].get("bay") == bay):
        return
    items = list_projects_in_bay(bay)
    st.session_state.active_project_by_bay[bay] = items[0][0] if items else None


def switch_bay(target_bay: str) -> None:
    if in_workspace_mode():
        save_workspace_from_session()
    else:
        save_session_into_project()

    st.session_state.active_bay = target_bay
    ensure_bay_has_active_project(target_bay)
    pid = st.session_state.active_project_by_bay.get(target_bay)

    if pid:
        load_project_into_session(pid)
        st.session_state.voice_status = f"{target_bay}: {st.session_state.project_title}"
    else:
        st.session_state.project_id = None
        st.session_state.project_title = "—"
        if target_bay == "NEW":
            load_workspace_into_session()
            st.session_state.voice_status = "NEW: (Story Bible workspace)"
        else:
            st.session_state.main_text = ""
            st.session_state.synopsis = ""
            st.session_state.genre_style_notes = ""
            st.session_state.world = ""
            st.session_state.characters = ""
            st.session_state.outline = ""
            st.session_state.voice_sample = ""
            st.session_state.ai_intensity = 0.75
            st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
            st.session_state.voices_seeded = True
            st.session_state.voice_status = f"{target_bay}: (empty)"

    st.session_state.last_action = f"Bay → {target_bay}"


def create_project_from_current_bible(title: str) -> str:
    title = title.strip() if title.strip() else f"New Project {now_ts()}"
    source = "workspace" if in_workspace_mode() else "clone"

    source_story_bible_id = None
    source_story_bible_created_ts = None
    if source == "workspace":
        w = st.session_state.sb_workspace or default_story_bible_workspace()
        source_story_bible_id = w.get("workspace_story_bible_id")
        source_story_bible_created_ts = w.get("workspace_story_bible_created_ts")
    else:
        pid = st.session_state.project_id
        if pid and pid in (st.session_state.projects or {}):
            source_story_bible_id = st.session_state.projects[pid].get("story_bible_id")

    p = new_project_payload(title)
    p["bay"] = "NEW"
    p["draft"] = st.session_state.main_text
    p["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }

    if source == "workspace" and source_story_bible_id:
        p["story_bible_id"] = source_story_bible_id
        if source_story_bible_created_ts:
            p["story_bible_created_ts"] = source_story_bible_created_ts

    p["story_bible_binding"] = {
        "locked": True,
        "locked_ts": now_ts(),
        "source": source,
        "source_story_bible_id": source_story_bible_id,
    }
    p["story_bible_fingerprint"] = _fingerprint_story_bible(p["story_bible"])

    # Voice templates + intensity
    p["voice_bible"]["voice_sample"] = st.session_state.voice_sample
    p["voice_bible"]["ai_intensity"] = float(st.session_state.ai_intensity)
    p["voices"] = compact_voice_vault(st.session_state.voices)
    p["style_banks"] = compact_style_banks(st.session_state.get("style_banks") or rebuild_vectors_in_style_banks(default_style_banks()))

    st.session_state.projects[p["id"]] = p
    st.session_state.active_project_by_bay["NEW"] = p["id"]

    if source == "workspace":
        reset_workspace_story_bible(keep_templates=True)
st.rerun()

    return p["id"]



def promote_project(pid: str, to_bay: str) -> None:
    p = (st.session_state.projects or {}).get(pid)
    if not p:
        return
    p["bay"] = to_bay
    p["updated_ts"] = now_ts()


def next_bay(bay: str) -> Optional[str]:
    if bay == "NEW":
        return "ROUGH"
    if bay == "ROUGH":
        return "EDIT"
    if bay == "EDIT":
        return "FINAL"
    return None


# ============================================================
# AUTOSAVE (atomic + backup)
# ============================================================
def _payload() -> Dict[str, Any]:
    if in_workspace_mode():
        save_workspace_from_session()
    else:
        save_session_into_project()
    return {
        "meta": {"saved_at": now_ts(), "version": "olivetti-prod-stable-v1"},
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "sb_workspace": st.session_state.sb_workspace,
        "projects": st.session_state.projects,
    }


def _digest(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def save_all_to_disk(force: bool = False) -> None:
    """Autosave state to disk with an atomic write and a simple backup."""
    try:
        os.makedirs(AUTOSAVE_DIR, exist_ok=True)
        payload = _payload()
        dig = _digest(payload)
        if (not force) and dig == st.session_state.last_saved_digest:
            return

        tmp_path = AUTOSAVE_PATH + ".tmp"
        bak_path = AUTOSAVE_PATH + ".bak"

        try:
            if os.path.exists(AUTOSAVE_PATH):
                import shutil

                shutil.copy2(AUTOSAVE_PATH, bak_path)
        except Exception:
            pass

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, AUTOSAVE_PATH)

        st.session_state.last_saved_digest = dig
    except Exception as e:
        st.session_state.voice_status = f"Autosave warning: {e}"


def load_all_from_disk() -> None:
    main_path = AUTOSAVE_PATH
    bak_path = AUTOSAVE_PATH + ".bak"

    def _boot_new() -> None:
        st.session_state.sb_workspace = st.session_state.get("sb_workspace") or default_story_bible_workspace()
        switch_bay("NEW")

    if (not os.path.exists(main_path)) and (not os.path.exists(bak_path)):
        _boot_new()
        return

    payload = None
    loaded_from = "primary"
    last_err = None
    for path, label in ((main_path, "primary"), (bak_path, "backup")):
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            loaded_from = label
            break
        except Exception as e:
            last_err = e
            payload = None

    if payload is None:
        st.session_state.voice_status = f"Load warning: {last_err}"
        _boot_new()
        return

    try:
        projs = payload.get("projects", {})
        if isinstance(projs, dict):
            st.session_state.projects = projs

        apbb = payload.get("active_project_by_bay", {})
        if isinstance(apbb, dict):
            for b in BAYS:
                apbb.setdefault(b, None)
            st.session_state.active_project_by_bay = apbb

        w = payload.get("sb_workspace")
        if isinstance(w, dict) and w.get("workspace_story_bible_id"):
            st.session_state.sb_workspace = w
        else:
            st.session_state.sb_workspace = default_story_bible_workspace()

        # Migration guards
        for _, p in (st.session_state.projects or {}).items():
            if not isinstance(p, dict):
                continue
            ts = p.get("created_ts") or now_ts()
            title = p.get("title", "Untitled")
            p.setdefault("story_bible_id", hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12])
            p.setdefault("story_bible_created_ts", ts)
            if not isinstance(p.get("story_bible_binding"), dict):
                p["story_bible_binding"] = {"locked": True, "locked_ts": ts, "source": "system", "source_story_bible_id": None}
            p.setdefault("locks", {})
            if isinstance(p["locks"], dict):
                p["locks"].setdefault("sb_edit_unlocked", False)
                p["locks"].setdefault("story_bible_lock", True)
            p.setdefault("voices", default_voice_vault())
            p.setdefault("style_banks", default_style_banks())
            if "story_bible_fingerprint" not in p:
                try:
                    p["story_bible_fingerprint"] = _fingerprint_story_bible(p.get("story_bible", {}) or {})
                except Exception:
                    p["story_bible_fingerprint"] = ""

        ab = payload.get("active_bay", "NEW")
        if ab not in BAYS:
            ab = "NEW"
        st.session_state.active_bay = ab

        ensure_bay_has_active_project(ab)
        pid = st.session_state.active_project_by_bay.get(ab)
        if pid:
            load_project_into_session(pid)
        else:
            if ab == "NEW":
                load_workspace_into_session()
                st.session_state.voice_status = "NEW: (Story Bible workspace)"
            else:
                switch_bay(ab)

        saved_at = (payload.get("meta", {}) or {}).get("saved_at", "")
        src = "autosave" if loaded_from == "primary" else "backup autosave"
        st.session_state.voice_status = f"Loaded {src} ({saved_at})."
        st.session_state.last_saved_digest = _digest(_payload())
    except Exception as e:
        st.session_state.voice_status = f"Load warning: {e}"
        _boot_new()


if "did_load_autosave" not in st.session_state:
    st.session_state.did_load_autosave = True
    load_all_from_disk()


def autosave() -> None:
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")
    save_all_to_disk()


# ============================================================
# IMPORT / EXPORT
# ============================================================
def _read_uploaded_text(uploaded) -> Tuple[str, str]:
    """Read .txt/.md/.docx from Streamlit UploadedFile."""
    if uploaded is None:
        return "", ""
    name = getattr(uploaded, "name", "") or ""
    raw = uploaded.getvalue()
    if raw is None:
        return "", name
    if len(raw) > MAX_UPLOAD_BYTES:
        return "", name
    ext = os.path.splitext(name.lower())[1]

    if ext in (".txt", ".md", ".markdown", ".text", ""):
        try:
            return raw.decode("utf-8"), name
        except Exception:
            return raw.decode("utf-8", errors="ignore"), name

    if ext == ".docx":
        try:
            from docx import Document  # python-docx

            doc = Document(BytesIO(raw))
            parts = []
            for p in doc.paragraphs:
                t = (p.text or "").strip()
                if t:
                    parts.append(t)
            return "\n\n".join(parts), name
        except Exception:
            try:
                return raw.decode("utf-8", errors="ignore"), name
            except Exception:
                return "", name

    try:
        return raw.decode("utf-8", errors="ignore"), name
    except Exception:
        return "", name


def _sb_sections_from_text_heuristic(text: str) -> Dict[str, str]:
    t = _normalize_text(text)
    if not t:
        return {"synopsis": "", "genre_style_notes": "", "world": "", "characters": "", "outline": ""}

    heading_map = {
        "synopsis": ["synopsis", "premise", "logline"],
        "genre_style_notes": ["genre", "style", "tone", "voice"],
        "world": ["world", "setting", "lore"],
        "characters": ["characters", "cast"],
        "outline": ["outline", "beats", "plot", "structure"],
    }

    lines = t.splitlines()
    buckets = {k: [] for k in heading_map.keys()}
    current = None

    def _match_heading(line: str) -> Optional[str]:
        l = re.sub(r"^[#\-\*\s]+", "", (line or "").strip()).lower()
        l = re.sub(r"[:\-\s]+$", "", l)
        for key, aliases in heading_map.items():
            if any(l == a or l.startswith(a + " ") for a in aliases):
                return key
        return None

    for line in lines:
        key = _match_heading(line)
        if key:
            current = key
            continue
        if current:
            buckets[current].append(line)
        else:
            buckets["synopsis"].append(line)

    return {k: _normalize_text("\n".join(v)) for k, v in buckets.items()}


def _extract_json_object(s: str) -> Optional[Dict[str, Any]]:
    if not s:
        return None
    s2 = re.sub(r"^```(?:json)?\s*|\s*```$", "", s.strip(), flags=re.IGNORECASE | re.MULTILINE)
    m = re.search(r"\{.*\}", s2, flags=re.DOTALL)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def story_bible_markdown(title: str, sb: Dict[str, str], meta: Dict[str, Any]) -> str:
    t = title or "Untitled"

    def sec(h: str, k: str) -> str:
        body = (sb.get(k, "") or "").strip()
        return f"## {h}\n\n{body}\n" if body else f"## {h}\n\n\n"

    front = f"# Story Bible — {t}\n\n- Exported: {now_ts()}\n"
    for mk, mv in (meta or {}).items():
        front += f"- {mk}: {mv}\n"
    front += "\n"
    return front + "\n".join(
        [
            sec("Synopsis", "synopsis"),
            sec("Genre / Style Notes", "genre_style_notes"),
            sec("World", "world"),
            sec("Characters", "characters"),
            sec("Outline", "outline"),
        ]
    )


def draft_markdown(title: str, draft: str, meta: Dict[str, Any]) -> str:
    t = title or "Untitled"
    front = f"# Draft — {t}\n\n- Exported: {now_ts()}\n"
    for mk, mv in (meta or {}).items():
        front += f"- {mk}: {mv}\n"
    front += "\n---\n\n"
    return front + (draft or "")


def make_project_bundle(pid: str) -> Dict[str, Any]:
    p = (st.session_state.projects or {}).get(pid, {}) or {}
    return {"meta": {"exported_at": now_ts(), "type": "project_bundle", "version": "1"}, "project": p}


def make_library_bundle() -> Dict[str, Any]:
    if in_workspace_mode():
        save_workspace_from_session()
    else:
        save_session_into_project()
    return {
        "meta": {"exported_at": now_ts(), "type": "library_bundle", "version": "1"},
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "sb_workspace": st.session_state.sb_workspace,
        "projects": st.session_state.projects,
    }


def _new_pid_like(seed: str) -> str:
    return hashlib.md5(f"{seed}|{now_ts()}".encode("utf-8")).hexdigest()[:12]


def import_project_bundle(bundle: Dict[str, Any], target_bay: str = "NEW", rename: str = "") -> Optional[str]:
    if not isinstance(bundle, dict):
        return None
    proj = bundle.get("project")
    if not isinstance(proj, dict):
        return None

    pid = str(proj.get("id") or _new_pid_like("import"))
    if pid in (st.session_state.projects or {}):
        pid = _new_pid_like(pid)

    proj = json.loads(json.dumps(proj))
    proj["id"] = pid
    if rename.strip():
        proj["title"] = rename.strip()
    if target_bay in BAYS:
        proj["bay"] = target_bay
    proj["updated_ts"] = now_ts()

    ts = proj.get("created_ts") or now_ts()
    title = proj.get("title", "Untitled")
    proj.setdefault("story_bible_id", hashlib.md5(f"sb|{title}|{ts}".encode("utf-8")).hexdigest()[:12])
    proj.setdefault("story_bible_created_ts", ts)
    if not isinstance(proj.get("story_bible_binding"), dict):
        proj["story_bible_binding"] = {"locked": True, "locked_ts": ts, "source": "import", "source_story_bible_id": None}
    proj.setdefault("locks", {})
    if isinstance(proj["locks"], dict):
        proj["locks"].setdefault("sb_edit_unlocked", False)
        proj["locks"].setdefault("story_bible_lock", True)
    proj.setdefault("voices", default_voice_vault())
    proj.setdefault("style_banks", default_style_banks())
    proj.setdefault("story_bible_fingerprint", "")

    st.session_state.projects[pid] = proj
    st.session_state.active_project_by_bay[proj.get("bay", "NEW")] = pid
    return pid


def import_library_bundle(bundle: Dict[str, Any]) -> int:
    if not isinstance(bundle, dict):
        return 0
    projs = bundle.get("projects")
    if not isinstance(projs, dict):
        return 0
    imported = 0
    for _, proj in projs.items():
        if not isinstance(proj, dict):
            continue
        pid = import_project_bundle({"project": proj}, target_bay=proj.get("bay", "NEW"), rename="")
        if pid:
            imported += 1

    w = bundle.get("sb_workspace")
    if isinstance(w, dict) and w.get("workspace_story_bible_id"):
        cur = st.session_state.sb_workspace or default_story_bible_workspace()
        cur_sb = (cur.get("story_bible", {}) or {})
        cur_empty = not any((cur_sb.get(k, "") or "").strip() for k in ["synopsis", "genre_style_notes", "world", "characters", "outline"])
        if cur_empty:
            st.session_state.sb_workspace = w
    return imported


# ============================================================
# JUNK DRAWER COMMANDS
# ============================================================
CMD_FIND = re.compile(r"^\s*/find\s*:\s*(.+)$", re.IGNORECASE)
CMD_CREATE = re.compile(r"^\s*/create\s*:\s*(.+)$", re.IGNORECASE)
CMD_PROMOTE = re.compile(r"^\s*/promote\s*$", re.IGNORECASE)


def _run_find(term: str) -> str:
    term = (term or "").strip()
    if not term:
        return "Find: missing search term. Use /find: word"

    def _hits(label: str, text: str) -> List[str]:
        lines = (text or "").splitlines()
        out = []
        for i, line in enumerate(lines, start=1):
            if term.lower() in (line or "").lower():
                out.append(f"{label} L{i}: {line.strip()}")
            if len(out) >= 20:
                break
        return out

    hits = []
    hits += _hits("DRAFT", st.session_state.main_text)
    hits += _hits("SYNOPSIS", st.session_state.synopsis)
    hits += _hits("WORLD", st.session_state.world)
    hits += _hits("CHARS", st.session_state.characters)
    hits += _hits("OUTLINE", st.session_state.outline)

    if not hits:
        return f"Find: no matches for '{term}'."
    return "\n".join(hits[:30])


def handle_junk_commands() -> None:
    raw = (st.session_state.junk or "").strip()
    if not raw:
        return

    m = CMD_CREATE.match(raw)
    if m:
        title = m.group(1).strip()
        pid = create_project_from_current_bible(title)
        st.session_state.active_project_by_bay["NEW"] = pid
        st.session_state.active_bay = "NEW"
        load_project_into_session(pid)
        st.session_state.voice_status = f"Created project in NEW: {st.session_state.project_title}"
        st.session_state.last_action = "Create Project"
        st.session_state.junk = ""
        autosave()
        return

    if CMD_PROMOTE.match(raw):
        pid = st.session_state.project_id
        bay = st.session_state.active_bay
        nb = next_bay(bay)
        if not pid or not nb:
            st.session_state.tool_output = "Promote: no project selected, or already FINAL."
            st.session_state.voice_status = "Promote blocked."
            st.session_state.junk = ""
            autosave()
            return
        save_session_into_project()
        promote_project(pid, nb)
        st.session_state.active_project_by_bay[nb] = pid
        switch_bay(nb)
        st.session_state.voice_status = f"Promoted → {nb}: {st.session_state.project_title}"
        st.session_state.last_action = f"Promote → {nb}"
        st.session_state.junk = ""
        autosave()
        return

    m = CMD_FIND.match(raw)
    if m:
        st.session_state.tool_output = _clamp_text(_run_find(m.group(1)))
        st.session_state.voice_status = "Find complete"
        st.session_state.last_action = "Find"
        st.session_state.junk = ""
        autosave()
        return


# Run junk commands early (before widgets instantiate)
handle_junk_commands()


# ============================================================
# AI BRIEF + CALL
# ============================================================
def _story_bible_text() -> str:
    sb = []
    if (st.session_state.synopsis or "").strip():
        sb.append(f"SYNOPSIS:\n{st.session_state.synopsis.strip()}")
    if (st.session_state.genre_style_notes or "").strip():
        sb.append(f"GENRE/STYLE NOTES:\n{st.session_state.genre_style_notes.strip()}")
    if (st.session_state.world or "").strip():
        sb.append(f"WORLD:\n{st.session_state.world.strip()}")
    if (st.session_state.characters or "").strip():
        sb.append(f"CHARACTERS:\n{st.session_state.characters.strip()}")
    if (st.session_state.outline or "").strip():
        sb.append(f"OUTLINE:\n{st.session_state.outline.strip()}")
    return "\n\n".join(sb).strip() if sb else "— None provided —"


def build_partner_brief(action_name: str, lane: str) -> str:
    story_bible = _story_bible_text()
    vb = []
    if st.session_state.vb_style_on:
        vb.append(f"Writing Style: {st.session_state.writing_style} (intensity {st.session_state.style_intensity:.2f})")
    if st.session_state.vb_genre_on:
        vb.append(f"Genre Influence: {st.session_state.genre} (intensity {st.session_state.genre_intensity:.2f})")
    if st.session_state.vb_trained_on and st.session_state.trained_voice and st.session_state.trained_voice != "— None —":
        vb.append(f"Trained Voice: {st.session_state.trained_voice} (intensity {st.session_state.trained_intensity:.2f})")
    if st.session_state.vb_match_on and (st.session_state.voice_sample or "").strip():
        vb.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and (st.session_state.voice_lock_prompt or "").strip():
        vb.append(f"VOICE LOCK (strength {st.session_state.lock_intensity:.2f}):\n{st.session_state.voice_lock_prompt.strip()}")
    voice_controls = "\n\n".join(vb).strip() if vb else "— None enabled —"

    # Engine Style (trainable banks)
    style_name = (st.session_state.writing_style or "").strip().upper()
    style_directive = ""
    style_exemplars: List[str] = []
    if st.session_state.vb_style_on and style_name in ENGINE_STYLES:
        style_directive = engine_style_directive(style_name, float(st.session_state.style_intensity), lane)
        ctx2 = (st.session_state.main_text or "")[-2500:]
        q2 = ctx2 if ctx2.strip() else (st.session_state.synopsis or "")
        k = 1 + int(max(0.0, min(1.0, float(st.session_state.style_intensity))) * 2.0)
        style_exemplars = retrieve_style_exemplars(style_name, lane, q2, k=k)

    exemplars: List[str] = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv and tv != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]
        query = ctx if ctx.strip() else st.session_state.synopsis
        exemplars = retrieve_mixed_exemplars(tv, lane, query)
    ex_block = "\n\n---\n\n".join(exemplars) if exemplars else "— None —"
    style_ex_block = "\n\n---\n\n".join(style_exemplars) if style_exemplars else "— None —"

    ai_x = float(st.session_state.ai_intensity)
    return f"""
YOU ARE OLIVETTI: the author's personal writing and editing partner.
Professional output only. No UI talk. No process talk.

STORY BIBLE IS CANON + IDEA BANK.
When generating NEW material, pull at least 2 concrete specifics from the Story Bible.
Never contradict canon. Never add random characters/places unless Story Bible supports it.

LANE: {lane}

AI INTENSITY: {ai_x:.2f}
INTENSITY PROFILE: {intensity_profile(ai_x)}

VOICE CONTROLS:
{voice_controls}

ENGINE STYLE DIRECTIVE:
{style_directive if style_directive else "— None —"}

STYLE EXEMPLARS (mimic cadence/diction, not content):
{style_ex_block}

TRAINED EXEMPLARS (mimic patterns, not content):
{ex_block}

STORY BIBLE:
{story_bible}

ACTION: {action_name}
""".strip()


def call_openai(system_brief: str, user_task: str, text: str) -> str:
    """One place for all OpenAI calls (lazy client, key-guarded)."""
    api_key = require_openai_key()
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not installed. Add to requirements.txt: openai>=2.0.0") from e

    # Create client lazily (never at import-time).
    try:
        client = OpenAI(api_key=api_key, timeout=60)
    except TypeError:
        client = OpenAI(api_key=api_key)

    draft = (text or "").strip()
    user_msg = f"{user_task}\n\nDRAFT:\n{draft}"

    # Prefer Responses API when available; fall back to Chat Completions for compatibility.
    if hasattr(client, "responses"):
        try:
            resp = client.responses.create(
                model=OPENAI_MODEL,
                instructions=system_brief,
                input=user_msg,
                max_output_tokens=900,
            )
            out = (getattr(resp, "output_text", None) or "").strip()
            if out:
                return out
        except Exception:
            pass

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_brief},
            {"role": "user", "content": user_msg},
        ],
        temperature=temperature_from_intensity(st.session_state.ai_intensity),
    )
    return (resp.choices[0].message.content or "").strip()

def local_cleanup(text: str) -> str:
    t = (text or "")
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{4,}", "\n\n\n", t)
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r"([,.;:!?])([A-Za-z0-9])", r"\1 \2", t)
    t = re.sub(r"\.\.\.", "…", t)
    t = re.sub(r"\s*--\s*", " — ", t)
    t = re.sub(r"[ \t]{2,}", " ", t)
    return t.strip()


def sb_breakdown_ai(text: str) -> Dict[str, str]:
    prompt = """Break the provided source document into these Story Bible sections.
Return STRICT JSON with these exact keys:
synopsis, genre_style_notes, world, characters, outline

Rules:
- Use clear, concrete specifics (names, places, stakes).
- Preserve existing proper nouns from the text.
- If a section is unknown, return an empty string for it.
- No commentary. JSON only.
"""
    try:
        out = call_openai(
            system_brief="You are a precise literary analyst. You output only valid JSON.",
            user_task=prompt,
            text=text,
        )
        obj = _extract_json_object(out) or {}
        return {
            "synopsis": _normalize_text(str(obj.get("synopsis", ""))),
            "genre_style_notes": _normalize_text(str(obj.get("genre_style_notes", ""))),
            "world": _normalize_text(str(obj.get("world", ""))),
            "characters": _normalize_text(str(obj.get("characters", ""))),
            "outline": _normalize_text(str(obj.get("outline", ""))),
        }
    except Exception:
        return _sb_sections_from_text_heuristic(text)


def _merge_section(existing: str, incoming: str, mode: str) -> str:
    ex = (existing or "").strip()
    inc = (incoming or "").strip()
    if mode == "Replace":
        return inc
    if not ex:
        return inc
    if not inc:
        return ex
    return (ex + "\n\n" + inc).strip()


# ============================================================
# ACTIONS (queued for Streamlit safety)
# ============================================================
def partner_action(action: str) -> None:
    text = st.session_state.main_text or ""
    lane = current_lane_from_draft(text)
    brief = build_partner_brief(action, lane=lane)
    use_ai = bool(OPENAI_API_KEY)

    def apply_replace(result: str) -> None:
        if result and result.strip():
            st.session_state.main_text = result.strip()
            st.session_state.last_action = action
            autosave()

    def apply_append(result: str) -> None:
        if result and result.strip():
            if (st.session_state.main_text or "").strip():
                st.session_state.main_text = (st.session_state.main_text.rstrip() + "\n\n" + result.strip()).strip()
            else:
                st.session_state.main_text = result.strip()
            st.session_state.last_action = action
            autosave()

    try:
        if action == "Write":
            if use_ai:
                task = (
                    f"Continue decisively in lane ({lane}). Add 1–3 paragraphs that advance the scene. "
                    "MANDATORY: incorporate at least 2 Story Bible specifics. "
                    "No recap. No planning. Just prose."
                )
                out = call_openai(brief, task, text if text.strip() else "Start the opening.")
                apply_append(out)
            return

        if action == "Rewrite":
            if use_ai:
                task = f"Rewrite for professional quality in lane ({lane}). Preserve meaning and canon. Return full revised text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(local_cleanup(text))
            return

        if action == "Expand":
            if use_ai:
                task = f"Expand with meaningful depth in lane ({lane}). No padding. Preserve canon. Return full revised text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            return

        if action == "Rephrase":
            if use_ai:
                task = f"Replace the final sentence with a stronger one (same meaning) in lane ({lane}). Return full text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            return

        if action == "Describe":
            if use_ai:
                task = f"Add vivid controlled description in lane ({lane}). Preserve pace and canon. Return full revised text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            return

        if action in ("Spell", "Grammar"):
            cleaned = local_cleanup(text)
            if use_ai:
                task = "Copyedit spelling/grammar/punctuation. Preserve voice. Return full revised text."
                out = call_openai(brief, task, cleaned)
                apply_replace(out if out else cleaned)
            else:
                apply_replace(cleaned)
            return

        if action == "Synonym":
            # Tool output only (does not change draft)
            last = ""
            m = re.search(r"([A-Za-z']{3,})\W*$", text.strip())
            if m:
                last = m.group(1)
            if not last:
                st.session_state.tool_output = "Synonym: couldn't detect a target word (try ending with a word)."
                st.session_state.voice_status = "Synonym: no target"
                autosave()
                return
            if use_ai:
                task = (
                    f"Give 12 strong synonyms for '{last}'. "
                    "Group them by nuance (formal, punchy, poetic, archaic, etc). "
                    "No filler." 
                )
                out = call_openai(brief, task, text)
                st.session_state.tool_output = _clamp_text(out)
            else:
                st.session_state.tool_output = f"Synonym requires OPENAI_API_KEY (target word: {last})."
            st.session_state.voice_status = f"Synonym: {last}"
            st.session_state.last_action = "Synonym"
            autosave()
            return

        if action == "Sentence":
            # Tool output only
            last_sentence = ""
            sentences = re.split(r"(?<=[.!?])\s+", text.strip())
            if sentences:
                last_sentence = sentences[-1].strip()
            if not last_sentence:
                st.session_state.tool_output = "Sentence: couldn't detect a final sentence."
                st.session_state.voice_status = "Sentence: no target"
                autosave()
                return
            if use_ai:
                task = (
                    "Provide 8 alternative rewrites of the final sentence. "
                    "Keep meaning. Vary rhythm and diction. Return as a numbered list."
                )
                out = call_openai(brief, task, text)
                st.session_state.tool_output = _clamp_text(out)
            else:
                st.session_state.tool_output = "Sentence requires OPENAI_API_KEY."
            st.session_state.voice_status = "Sentence options"
            st.session_state.last_action = "Sentence"
            autosave()
            return

    except Exception as e:
        msg = str(e)
        if ("insufficient_quota" in msg) or ("exceeded your current quota" in msg.lower()):
            st.session_state.voice_status = "Engine: OpenAI quota exceeded."
            st.session_state.tool_output = _clamp_text(
                "OpenAI returned a quota/billing error.\n\nFix:\n• Confirm your API key is correct\n• Check billing/usage limits\n• Or swap to a different key in Streamlit Secrets"
            )
        elif "OPENAI_API_KEY not set" in msg:
            st.session_state.voice_status = "Engine: missing OPENAI_API_KEY."
            st.session_state.tool_output = "Set OPENAI_API_KEY in Streamlit Secrets (or environment) to enable AI."
        else:
            st.session_state.voice_status = f"Engine: {msg}"
            st.session_state.tool_output = _clamp_text(f"ERROR:\n{msg}")
        autosave()


def queue_action(action: str) -> None:
    st.session_state.pending_action = action


def cb_create_project() -> None:
    """Create a new project from the current Story Bible (runs as a pre-rerun callback)."""
    synopsis = (st.session_state.get("synopsis") or "").strip()
    title_guess = (synopsis.splitlines()[0].strip() if synopsis else "New Project")
    pid = create_project_from_current_bible(title_guess)
    load_project_into_session(pid)
    st.session_state.voice_status = f"Created in NEW: {st.session_state.project_title}"
    st.session_state.last_action = "Create Project"
    autosave()
    st.rerun()


def cb_new_workspace_bible() -> None:
    """Mint a fresh workspace Story Bible ID (workspace-only)."""
    reset_workspace_story_bible(keep_templates=True)
    
    st.session_state.voice_status = "Workspace: new Story Bible minted"
    st.session_state.last_action = "New Story Bible"
    autosave()
    st.rerun()


def cb_promote_to(target_bay: str) -> None:
    """Promote the active project to the target bay (pre-rerun callback)."""
    pid = st.session_state.get("project_id")
    if not pid:
        st.session_state.tool_output = "No active project to promote."
        autosave()
        return
    save_session_into_project()
    promote_project(pid, target_bay)
    st.session_state.active_project_by_bay[target_bay] = pid
    switch_bay(target_bay)
    st.session_state.voice_status = f"Promoted → {target_bay}: {st.session_state.project_title}"
    st.session_state.last_action = f"Promote → {target_bay}"
    autosave()


def cb_import_bundle() -> None:
    """Import a project/library bundle and optionally switch to it (pre-rerun callback)."""
    upb = st.session_state.get("io_bundle_upload")
    target_bay = st.session_state.get("io_bundle_target") or "NEW"
    rename = (st.session_state.get("io_bundle_rename") or "").strip()
    switch_after = bool(st.session_state.get("io_bundle_switch", True))

    if upb is None:
        st.session_state.tool_output = "Import bundle: upload a .json file first."
        autosave()
        return

    raw = upb.getvalue()
    if raw is not None and len(raw) > MAX_UPLOAD_BYTES:
        st.session_state.tool_output = "Import bundle: file too large."
        autosave()
        return

    try:
        obj = json.loads((raw or b"").decode("utf-8"))
    except Exception:
        obj = None

    if isinstance(obj, dict) and obj.get("projects"):
        n = import_library_bundle(obj)
        st.session_state.voice_status = f"Imported library bundle: {n} projects merged."
        st.session_state.last_action = "Import Library Bundle"
        autosave()
        return

    if isinstance(obj, dict) and obj.get("project"):
        pid = import_project_bundle(obj, target_bay=target_bay, rename=rename)
        if not pid:
            st.session_state.tool_output = "Import bundle: JSON did not look like a project bundle."
            autosave()
            return
        st.session_state.voice_status = f"Imported project bundle → {pid}"
        st.session_state.last_action = "Import Project Bundle"
        autosave()
        if switch_after:
            st.session_state.active_project_by_bay[target_bay] = pid
            switch_bay(target_bay)
            load_project_into_session(pid)
            st.session_state.voice_status = f"{target_bay}: {st.session_state.project_title} (imported)"
            autosave()
        return

    st.session_state.tool_output = "Import bundle: bundle type not recognized."
    autosave()


def cb_style_delete_last() -> None:
    st_style = (st.session_state.get("style_train_style") or "").strip()
    st_lane = (st.session_state.get("style_train_lane") or "Narration")
    if delete_last_style_sample(st_style, st_lane):
        st.session_state.voice_status = f"Style Trainer: deleted last → {st_style} • {st_lane}"
    else:
        st.session_state.tool_output = "Style Trainer: nothing to delete for that style/lane."
    autosave()


def cb_style_clear_text() -> None:
    st.session_state.style_train_paste = ""
    st.session_state.voice_status = "Style Trainer: text cleared."
    autosave()


def cb_style_clear_lane() -> None:
    st_style = (st.session_state.get("style_train_style") or "").strip()
    st_lane = (st.session_state.get("style_train_lane") or "Narration")
    clear_style_lane(st_style, st_lane)
    st.session_state.voice_status = f"Style Trainer: cleared lane → {st_style} • {st_lane}"
    autosave()


def cb_vault_create_voice() -> None:
    name = (st.session_state.get("vault_new_voice") or "").strip()
    if create_custom_voice(name):
        st.session_state.vault_voice_sel = name
        st.session_state.voice_status = f"Voice created: {name}"
    else:
        st.session_state.tool_output = "Could not create that voice (empty or already exists)."
    autosave()


def cb_vault_add_sample() -> None:
    voice = (st.session_state.get("vault_voice_sel") or "").strip()
    lane = (st.session_state.get("vault_lane_sel") or "Narration")
    sample = (st.session_state.get("vault_sample_text") or "").strip()
    if add_voice_sample(voice, lane, sample):
        st.session_state.vault_sample_text = ""
        st.session_state.voice_status = f"Added sample → {voice} • {lane}"
    else:
        st.session_state.tool_output = "No sample text found."
    autosave()


def cb_vault_delete_last_sample() -> None:
    voice = (st.session_state.get("vault_voice_sel") or "").strip()
    lane = (st.session_state.get("vault_lane_sel") or "Narration")
    if delete_voice_sample(voice, lane, index_from_end=0):
        st.session_state.voice_status = f"Deleted last sample → {voice} • {lane}"
    else:
        st.session_state.tool_output = "Nothing to delete for that lane."
    autosave()



def run_pending_action() -> None:
    action = st.session_state.get("pending_action")
    if not action:
        return
    st.session_state.pending_action = None

    # Non-engine UI hint (keeps session_state mutations pre-widget)
    if action == "__FIND_HINT__":
        st.session_state.tool_output = "Find is wired via /find: in Junk Drawer."
        st.session_state.voice_status = "Find: use /find: in Junk Drawer."
        st.session_state.last_action = "Find (hint)"
        autosave()
        return

    if action == "__VAULT_CLEAR_SAMPLE__":
        # Clear the vault sample text area safely (pre-widget) and surface status.
        st.session_state.vault_sample_text = ""
        note = (st.session_state.get("ui_notice") or "").strip()
        if note:
            st.session_state.voice_status = note
            st.session_state.ui_notice = ""
        st.session_state.last_action = "Voice Vault"
        autosave()
        return
    partner_action(action)


# Run queued actions early (pre-widget)
run_pending_action()


# ============================================================
# UI — TOP BAR
# ============================================================
top = st.container()
with top:
    cols = st.columns([1, 1, 1, 1, 2])

    if cols[0].button("🆕 New", key="bay_new"):
        switch_bay("NEW")
        save_all_to_disk(force=True)

    if cols[1].button("✏️ Rough", key="bay_rough"):
        switch_bay("ROUGH")
        save_all_to_disk(force=True)

    if cols[2].button("🛠 Edit", key="bay_edit"):
        switch_bay("EDIT")
        save_all_to_disk(force=True)

    if cols[3].button("✅ Final", key="bay_final"):
        switch_bay("FINAL")
        save_all_to_disk(force=True)

    cols[4].markdown(
        f"""
        <div style='text-align:right;font-size:12px;'>
            Bay: <b>{st.session_state.active_bay}</b>
            &nbsp;•&nbsp; Project: <b>{st.session_state.project_title}</b>
            &nbsp;•&nbsp; Autosave: {st.session_state.autosave_time or '—'}
            <br/>AI Intensity: {float(st.session_state.ai_intensity):.2f}
            &nbsp;•&nbsp; Status: {st.session_state.voice_status}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ============================================================
# LOCKED LAYOUT (same ratios)
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.6])


# ============================================================
# LEFT — STORY BIBLE
# ============================================================
with left:
    st.subheader("📖 Story Bible")

    bay = st.session_state.active_bay
    bay_projects = list_projects_in_bay(bay)

    # Build a stable selector with unique labels (handles duplicate titles)
    if bay == "NEW":
        items: List[Tuple[Optional[str], str]] = [(None, "— (Story Bible workspace) —")] + [(pid, title) for pid, title in bay_projects]
    else:
        items = [(None, "— (none) —")] + [(pid, title) for pid, title in bay_projects]

    # Disambiguate duplicate titles
    seen: Dict[str, int] = {}
    labels: List[str] = []
    ids: List[Optional[str]] = []
    for pid, title in items:
        base = title
        seen[base] = seen.get(base, 0) + 1
        label = base if seen[base] == 1 else f"{base}  ·  {str(pid)[-4:]}"
        labels.append(label)
        ids.append(pid)

    current_pid = st.session_state.project_id if (st.session_state.project_id in ids) else None
    current_idx = ids.index(current_pid) if current_pid in ids else 0

    sel = st.selectbox("Current Bay Project", labels, index=current_idx, key="bay_project_selector")
    sel_pid = ids[labels.index(sel)] if sel in labels else None

    if sel_pid:
        p = st.session_state.projects.get(sel_pid, {}) or {}
        sbid = p.get("story_bible_id", "—")
        sbts = p.get("story_bible_created_ts", "—")
        bind = p.get("story_bible_binding", {}) or {}
        src = bind.get("source", "—")
        st.caption(f"Locked Story Bible → Project • Bible ID: **{sbid}** • Created: **{sbts}** • Source: **{src}**")
    else:
        w = st.session_state.sb_workspace or default_story_bible_workspace()
        st.caption(
            f"Workspace Story Bible (not linked yet) • Bible ID: **{w.get('workspace_story_bible_id','—')}** • Created: **{w.get('workspace_story_bible_created_ts','—')}**"
        )

    # Switch context if changed
    if sel_pid != st.session_state.project_id:
        if in_workspace_mode():
            save_workspace_from_session()
        else:
            save_session_into_project()

        st.session_state.active_project_by_bay[bay] = sel_pid
        if sel_pid:
            load_project_into_session(sel_pid)
            st.session_state.voice_status = f"{bay}: {st.session_state.project_title}"
        else:
            st.session_state.project_id = None
            st.session_state.project_title = "—"
            if bay == "NEW":
                load_workspace_into_session()
                st.session_state.voice_status = "NEW: (Story Bible workspace)"
            else:
                st.session_state.main_text = ""
                st.session_state.synopsis = ""
                st.session_state.genre_style_notes = ""
                st.session_state.world = ""
                st.session_state.characters = ""
                st.session_state.outline = ""
                st.session_state.voice_sample = ""
                st.session_state.ai_intensity = 0.75
                st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
                st.session_state.voices_seeded = True
                st.session_state.voice_status = f"{bay}: (empty)"
        st.session_state.last_action = "Select Context"
        autosave()

    # Hard lock: Story Bible edits are locked per-project unless explicitly unlocked
    is_project = bool(st.session_state.project_id)
    sb_edit_unlocked = bool((st.session_state.locks or {}).get("sb_edit_unlocked", False))
    sb_locked = is_project and (not sb_edit_unlocked)

    with st.expander("🔒 Story Bible Hard Lock", expanded=False):
        if is_project:
            st.caption("Default is LOCKED. Unlock only when you intend to edit canon.")
            st.checkbox("Unlock Story Bible Editing", key="sb_unlock_cb")
            # sync the checkbox into locks
            st.session_state.locks["sb_edit_unlocked"] = bool(st.session_state.sb_unlock_cb)
            autosave()
        else:
            st.caption("Workspace is always editable. This lock applies after a project is created.")

    # ✅ AI Intensity lives in Story Bible panel (left)
    st.slider(
        "AI Intensity",
        0.0,
        1.0,
        key="ai_intensity",
        help="0.0 = conservative/precise, 1.0 = bold/creative. Applies to every AI generation.",
        on_change=autosave,
    )

    # Project controls
    action_cols = st.columns([1, 1])
    if bay == "NEW":
        label = "Start Project (Lock Bible → Project)" if in_workspace_mode() else "Create Project (from Bible)"
        action_cols[0].button(label, key="create_project_btn", on_click=cb_create_project)

        if in_workspace_mode():
            action_cols[1].button("New Story Bible (fresh ID)", key="new_workspace_bible_btn", on_click=cb_new_workspace_bible)

        action_cols[1].button("Promote → Rough", key="promote_new_to_rough", on_click=cb_promote_to, args=("ROUGH",))
    elif bay in ("ROUGH", "EDIT"):
        nb = next_bay(bay)
        action_cols[1].button(f"Promote → {nb.title()}", key=f"promote_{bay.lower()}", on_click=cb_promote_to, args=(nb,))

    st.divider()

    st.checkbox("Enable Genre Influence", key="vb_genre_on", on_change=autosave)
    st.selectbox(
        "Genre",
        ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
        key="genre",
        disabled=not st.session_state.vb_genre_on,
        on_change=autosave,
    )
    st.slider("Genre Intensity", 0.0, 1.0, key="genre_intensity", disabled=not st.session_state.vb_genre_on, on_change=autosave)

    st.divider()

    st.checkbox("Enable Trained Voice", key="vb_trained_on", on_change=autosave)
    trained_options = voice_names_for_selector()
    if st.session_state.trained_voice not in trained_options:
        st.session_state.trained_voice = "— None —"
    st.selectbox(
        "Trained Voice",
        trained_options,
        key="trained_voice",
        disabled=not st.session_state.vb_trained_on,
        on_change=autosave,
    )
    st.slider(
        "Trained Voice Intensity",
        0.0,
        1.0,
        key="trained_intensity",
        disabled=not st.session_state.vb_trained_on,
        on_change=autosave,
    )

    with st.expander("🧬 Voice Vault (Training Samples)", expanded=False):
        st.caption("Drop in passages from your work. Olivetti retrieves the closest exemplars per lane.")

        existing_voices = [v for v in (st.session_state.voices or {}).keys()]
        existing_voices = sorted(existing_voices, key=lambda x: (x not in ("Voice A", "Voice B"), x))
        if not existing_voices:
            existing_voices = ["Voice A", "Voice B"]

        vcol1, vcol2 = st.columns([2, 1])
        vault_voice = vcol1.selectbox("Vault voice", existing_voices, key="vault_voice_sel")
        new_name = vcol2.text_input("New voice", key="vault_new_voice", label_visibility="collapsed", placeholder="New voice name")
        vcol2.button("Create", key="vault_create_voice", on_click=cb_vault_create_voice)

        lane = st.selectbox("Lane", LANES, key="vault_lane_sel")
        sample = st.text_area("Sample", key="vault_sample_text", height=140, label_visibility="collapsed", placeholder="Paste a passage...")
        a1, a2 = st.columns([1, 1])
        a1.button("Add sample", key="vault_add_sample", on_click=cb_vault_add_sample)

        # Quick stats + delete last sample
        v = (st.session_state.voices or {}).get(vault_voice, {})
        lane_counts = {ln: len((v.get("lanes", {}) or {}).get(ln, []) or []) for ln in LANES}
        st.caption("Samples: " + "  ".join([f"{ln}: {lane_counts[ln]}" for ln in LANES]))

        a2.button("Delete last sample", key="vault_del_last", on_click=cb_vault_delete_last_sample)

    st.divider()

    st.checkbox("Enable Match My Style", key="vb_match_on", on_change=autosave)
    st.text_area(
        "Style Example",
        key="voice_sample",
        height=100,
        disabled=not st.session_state.vb_match_on,
        on_change=autosave,
    )
    st.slider("Match Intensity", 0.0, 1.0, key="match_intensity", disabled=not st.session_state.vb_match_on, on_change=autosave)

    st.divider()

    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on", on_change=autosave)
    st.text_area(
        "Voice Lock Prompt",
        key="voice_lock_prompt",
        height=80,
        disabled=not st.session_state.vb_lock_on,
        on_change=autosave,
    )
    st.slider("Lock Strength", 0.0, 1.0, key="lock_intensity", disabled=not st.session_state.vb_lock_on, on_change=autosave)

    st.divider()

    st.selectbox("POV", ["First", "Close Third", "Omniscient"], key="pov", on_change=autosave)
    st.selectbox("Tense", ["Past", "Present"], key="tense", on_change=autosave)


# ============================================================
# SAFETY NET SAVE EVERY RERUN
# ============================================================
save_all_to_disk()
