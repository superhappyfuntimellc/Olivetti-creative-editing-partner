import os
import re
import math
import json
import hashlib
import streamlit as st
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

# ============================================================
# ENV / METADATA HYGIENE
# ============================================================
os.environ.setdefault("MS_APP_ID", "olivetti-writing-desk")
os.environ.setdefault("ms-appid", "olivetti-writing-desk")

DEFAULT_MODEL = "gpt-5"
try:
    OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")  # type: ignore[attr-defined]
    OPENAI_MODEL = st.secrets.get("OPENAI_MODEL", DEFAULT_MODEL)  # type: ignore[attr-defined]
except Exception:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(page_title="Olivetti Desk", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    div[data-testid="stTextArea"] textarea {
      font-size: 18px !important;
      line-height: 1.65 !important;
      padding: 18px !important;
      resize: vertical !important;
      min-height: 520px !important;
    }
    button[kind="secondary"], button[kind="primary"] {
      font-size: 16px !important;
      padding: 0.6rem 0.9rem !important;
    }
    label, .stSelectbox label, .stSlider label { font-size: 14px !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# GLOBALS
# ============================================================
LANES = ["Dialogue", "Narration", "Interiority", "Action"]
BAYS = ["NEW", "ROUGH", "EDIT", "FINAL"]  # work bays
AUTOSAVE_DIR = "autosave"
AUTOSAVE_PATH = os.path.join(AUTOSAVE_DIR, "olivetti_state.json")

WORD_RE = re.compile(r"[A-Za-z']+")

# ============================================================
# UTILS
# ============================================================
def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

def _join_paragraphs(paras: List[str]) -> str:
    return ("\n\n".join([p.strip() for p in paras if p is not None])).strip()

# ============================================================
# LANE DETECTION (lightweight)
# ============================================================
THOUGHT_WORDS = {
    "think","thought","felt","wondered","realized","remembered","knew","noticed","decided",
    "hoped","feared","wanted","imagined","could","should","would"
}
ACTION_VERBS = {
    "run","ran","walk","walked","grab","grabbed","push","pushed","pull","pulled","slam","slammed",
    "hit","struck","kick","kicked","turn","turned","snap","snapped","dive","dived","duck","ducked",
    "rush","rushed","lunge","lunged","climb","climbed","drop","dropped","throw","threw","fire","fired",
    "aim","aimed","break","broke","shatter","shattered","step","stepped","move","moved","reach","reached"
}

def detect_lane(paragraph: str) -> str:
    p = (paragraph or "").strip()
    if not p:
        return "Narration"

    quote_count = p.count('"') + p.count("“") + p.count("”")
    has_dialogue_punct = (p.startswith("—") or p.startswith("- ") or p.startswith("“") or p.startswith('"'))

    dialogue_score = 0.0
    if quote_count >= 2: dialogue_score += 2.5
    if has_dialogue_punct: dialogue_score += 1.5

    toks = _tokenize(p)
    interior_score = 0.0
    if toks:
        first_person = sum(1 for t in toks if t in ("i","me","my","mine","myself"))
        thought_hits = sum(1 for t in toks if t in THOUGHT_WORDS)
        if first_person >= 2 and thought_hits >= 1: interior_score += 2.2

    action_score = 0.0
    if toks:
        verb_hits = sum(1 for t in toks if t in ACTION_VERBS)
        if verb_hits >= 2: action_score += 1.6
        if "!" in p: action_score += 0.3

    scores = {"Dialogue": dialogue_score, "Interiority": interior_score, "Action": action_score, "Narration": 0.25}
    lane = max(scores.items(), key=lambda kv: kv[1])[0]
    return "Narration" if scores[lane] < 0.9 else lane

def current_lane_from_draft(text: str) -> str:
    paras = _split_paragraphs(text)
    if not paras:
        return "Narration"
    return detect_lane(paras[-1])

# ============================================================
# PROJECT MODEL
# ============================================================
def default_voice_vault() -> Dict[str, Any]:
    ts = now_ts()
    return {
        "Voice A": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
        "Voice B": {"created_ts": ts, "lanes": {ln: [] for ln in LANES}},
    }

def new_project_payload(title: str) -> Dict[str, Any]:
    return {
        "id": hashlib.md5(f"{title}|{now_ts()}".encode("utf-8")).hexdigest()[:12],
        "title": title.strip() if title.strip() else "Untitled Project",
        "created_ts": now_ts(),
        "updated_ts": now_ts(),
        "bay": "NEW",
        "draft": "",
        "story_bible": {
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        },
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
        },
        "locks": {
            "story_bible_lock": True,
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },
        "voices": default_voice_vault(),  # compact: store only text+ts; vectors rebuilt in session
    }

# ============================================================
# SESSION INIT
# ============================================================
def init_state():
    defaults = {
        # current work bay shown by top bar
        "active_bay": "NEW",

        # project registry
        "projects": {},  # id -> project dict

        # per-bay active project id (what you're currently working on in each bay)
        "active_project_by_bay": {b: None for b in BAYS},

        # working fields (mirror the selected project in the active bay)
        "project_id": None,
        "project_title": "—",
        "autosave_time": None,
        "last_action": "—",
        "voice_status": "—",

        # writing + story bible
        "main_text": "",
        "synopsis": "",
        "genre_style_notes": "",
        "world": "",
        "characters": "",
        "outline": "",

        # junk + tool output
        "junk": "",
        "tool_output": "",

        # voice bible
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

        # locks
        "locks": {
            "story_bible_lock": True,
            "voice_fingerprint_lock": True,
            "lane_lock": False,
            "forced_lane": "Narration",
        },

        # voice vault (session expanded with vectors)
        "voices": {},
        "voices_seeded": False,

        # history
        "revisions": [],
        "redo_stack": [],

        # digests
        "last_saved_digest": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# PROJECT <-> SESSION SYNC
# ============================================================
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
            lanes_out[ln] = [{"ts": s.get("ts"), "text": s.get("text", "")} for s in samples if s.get("text")]
        out[vname] = {"created_ts": v.get("created_ts"), "lanes": lanes_out}
    return out

def load_project_into_session(pid: str) -> None:
    p = st.session_state.projects.get(pid)
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
        "vb_style_on","vb_genre_on","vb_trained_on","vb_match_on","vb_lock_on",
        "writing_style","genre","trained_voice","voice_sample","voice_lock_prompt",
        "style_intensity","genre_intensity","trained_intensity","match_intensity","lock_intensity",
        "pov","tense"
    ]:
        if k in vb:
            st.session_state[k] = vb[k]

    locks = p.get("locks", {}) or {}
    if isinstance(locks, dict):
        st.session_state.locks = locks

    st.session_state.voices = rebuild_vectors_in_voice_vault(p.get("voices", default_voice_vault()))
    st.session_state.voices_seeded = True

def save_session_into_project() -> None:
    pid = st.session_state.project_id
    if not pid:
        return
    p = st.session_state.projects.get(pid)
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
    }
    p["locks"] = st.session_state.locks
    p["voices"] = compact_voice_vault(st.session_state.voices)

def list_projects_in_bay(bay: str) -> List[Tuple[str, str]]:
    items = []
    for pid, p in (st.session_state.projects or {}).items():
        if p.get("bay") == bay:
            title = p.get("title", "Untitled")
            items.append((pid, title))
    items.sort(key=lambda x: x[1].lower())
    return items

def ensure_bay_has_active_project(bay: str) -> None:
    # if bay has active id and exists, keep it
    pid = st.session_state.active_project_by_bay.get(bay)
    if pid and pid in st.session_state.projects and st.session_state.projects[pid].get("bay") == bay:
        return

    # else pick first in bay
    items = list_projects_in_bay(bay)
    if items:
        st.session_state.active_project_by_bay[bay] = items[0][0]
        return

    # NEW bay may start empty; other bays can be empty too.
    st.session_state.active_project_by_bay[bay] = None

def switch_bay(target_bay: str) -> None:
    # save current working project first
    save_session_into_project()
    # set active bay
    st.session_state.active_bay = target_bay
    # ensure we have a project selected for that bay
    ensure_bay_has_active_project(target_bay)
    pid = st.session_state.active_project_by_bay.get(target_bay)
    if pid:
        load_project_into_session(pid)
        st.session_state.voice_status = f"{target_bay}: {st.session_state.project_title}"
    else:
        # no project in this bay yet; clear session workspace
        st.session_state.project_id = None
        st.session_state.project_title = "—"
        st.session_state.main_text = ""
        st.session_state.synopsis = ""
        st.session_state.genre_style_notes = ""
        st.session_state.world = ""
        st.session_state.characters = ""
        st.session_state.outline = ""
        st.session_state.voice_sample = ""
        st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
        st.session_state.voices_seeded = True
        st.session_state.voice_status = f"{target_bay}: (empty)"
    st.session_state.last_action = f"Bay → {target_bay}"

def create_project_from_current_bible(title: str) -> str:
    title = title.strip() if title.strip() else f"New Project {now_ts()}"
    p = new_project_payload(title)
    p["bay"] = "NEW"

    # initialize from current session bible/draft (builder workflow)
    p["draft"] = st.session_state.main_text
    p["story_bible"] = {
        "synopsis": st.session_state.synopsis,
        "genre_style_notes": st.session_state.genre_style_notes,
        "world": st.session_state.world,
        "characters": st.session_state.characters,
        "outline": st.session_state.outline,
    }
    p["voice_bible"]["voice_sample"] = st.session_state.voice_sample
    p["voices"] = compact_voice_vault(st.session_state.voices)

    st.session_state.projects[p["id"]] = p
    st.session_state.active_project_by_bay["NEW"] = p["id"]
    return p["id"]

def promote_project(pid: str, to_bay: str) -> None:
    p = st.session_state.projects.get(pid)
    if not p:
        return
    p["bay"] = to_bay
    p["updated_ts"] = now_ts()

# ============================================================
# AUTOSAVE ALL
# ============================================================
def _payload() -> Dict[str, Any]:
    # always persist current session back into current project before saving
    save_session_into_project()
    return {
        "meta": {"saved_at": now_ts(), "version": "olivetti-bays-v1"},
        "active_bay": st.session_state.active_bay,
        "active_project_by_bay": st.session_state.active_project_by_bay,
        "projects": st.session_state.projects,
    }

def _digest(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def save_all_to_disk(force: bool = False) -> None:
    try:
        os.makedirs(AUTOSAVE_DIR, exist_ok=True)
        payload = _payload()
        dig = _digest(payload)
        if (not force) and dig == st.session_state.last_saved_digest:
            return
        with open(AUTOSAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        st.session_state.last_saved_digest = dig
    except Exception as e:
        st.session_state.voice_status = f"Autosave warning: {e}"

def load_all_from_disk() -> None:
    if not os.path.exists(AUTOSAVE_PATH):
        # start with empty bays; stay in NEW
        switch_bay("NEW")
        return
    try:
        with open(AUTOSAVE_PATH, "r", encoding="utf-8") as f:
            payload = json.load(f)

        projs = payload.get("projects", {})
        if isinstance(projs, dict):
            st.session_state.projects = projs

        apbb = payload.get("active_project_by_bay", {})
        if isinstance(apbb, dict):
            # ensure all bays exist
            for b in BAYS:
                if b not in apbb:
                    apbb[b] = None
            st.session_state.active_project_by_bay = apbb

        ab = payload.get("active_bay", "NEW")
        if ab not in BAYS:
            ab = "NEW"
        st.session_state.active_bay = ab

        # load active project in that bay
        ensure_bay_has_active_project(ab)
        pid = st.session_state.active_project_by_bay.get(ab)
        if pid:
            load_project_into_session(pid)
        else:
            switch_bay(ab)

        st.session_state.voice_status = f"Loaded autosave ({payload.get('meta', {}).get('saved_at','')})."
        st.session_state.last_saved_digest = _digest(_payload())
    except Exception as e:
        st.session_state.voice_status = f"Load warning: {e}"
        switch_bay("NEW")

if "did_load_autosave" not in st.session_state:
    st.session_state.did_load_autosave = True
    load_all_from_disk()

def autosave():
    st.session_state.autosave_time = datetime.now().strftime("%H:%M:%S")
    save_all_to_disk()

# ============================================================
# VOICE VAULT OPS
# ============================================================
def seed_default_voices():
    if st.session_state.voices_seeded:
        return
    st.session_state.voices = rebuild_vectors_in_voice_vault(default_voice_vault())
    st.session_state.voices_seeded = True

seed_default_voices()

def ensure_voice(name: str):
    nm = (name or "").strip()
    if not nm:
        return
    if nm not in st.session_state.voices:
        st.session_state.voices[nm] = {"created_ts": now_ts(), "lanes": {ln: [] for ln in LANES}}

def voice_names_for_selector() -> List[str]:
    base = ["— None —", "Voice A", "Voice B"]
    customs = sorted([k for k in st.session_state.voices.keys() if k not in ("Voice A", "Voice B")])
    return base + customs

def _cap_lane_samples(voice_name: str, lane: str, cap: int = 160):
    v = st.session_state.voices.get(voice_name)
    if not v:
        return
    v["lanes"][lane] = v["lanes"][lane][-cap:]

def add_sample_to_voice_lane(voice_name: str, lane: str, sample_text: str) -> None:
    ensure_voice(voice_name)
    lane = lane if lane in LANES else "Narration"
    txt = _normalize_text(sample_text)
    if len(txt) < 180:
        return
    st.session_state.voices[voice_name]["lanes"][lane].append({"ts": now_ts(), "text": txt, "vec": _hash_vec(txt)})
    _cap_lane_samples(voice_name, lane)

def import_samples_to_voice(voice_name: str, big_sample: str) -> Tuple[int, Dict[str, int]]:
    ensure_voice(voice_name)
    text = _normalize_text(big_sample)
    paras = _split_paragraphs(text)

    merged: List[str] = []
    buf = ""
    for p in paras:
        if len(p) < 160:
            buf = (buf + "\n\n" + p).strip() if buf else p
            continue
        if buf:
            merged.append(buf.strip()); buf = ""
        merged.append(p)
    if buf:
        merged.append(buf.strip())

    counts = {ln: 0 for ln in LANES}
    imported = 0
    for p in merged:
        if len(p) < 180:
            continue
        lane = detect_lane(p)
        add_sample_to_voice_lane(voice_name, lane, p)
        counts[lane] += 1
        imported += 1

    for ln in LANES:
        _cap_lane_samples(voice_name, ln, cap=160)
    return imported, counts

def delete_voice(name: str) -> str:
    nm = (name or "").strip()
    if nm in ("Voice A", "Voice B"):
        for ln in LANES:
            st.session_state.voices[nm]["lanes"][ln] = []
        return f"Cleared samples for {nm}."
    if nm in st.session_state.voices:
        del st.session_state.voices[nm]
        return f"Deleted voice: {nm}"
    return "Voice not found."

def retrieve_exemplars(voice_name: str, lane: str, query_text: str, k: int = 3) -> List[str]:
    v = st.session_state.voices.get(voice_name)
    if not v:
        return []
    lane = lane if lane in LANES else "Narration"
    pool = v["lanes"].get(lane, [])
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
# AI BRIEF (kept lean; always Story Bible)
# ============================================================
def _story_bible_text() -> str:
    sb = []
    if st.session_state.synopsis.strip(): sb.append(f"SYNOPSIS:\n{st.session_state.synopsis.strip()}")
    if st.session_state.genre_style_notes.strip(): sb.append(f"GENRE/STYLE NOTES:\n{st.session_state.genre_style_notes.strip()}")
    if st.session_state.world.strip(): sb.append(f"WORLD:\n{st.session_state.world.strip()}")
    if st.session_state.characters.strip(): sb.append(f"CHARACTERS:\n{st.session_state.characters.strip()}")
    if st.session_state.outline.strip(): sb.append(f"OUTLINE:\n{st.session_state.outline.strip()}")
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
    if st.session_state.vb_match_on and st.session_state.voice_sample.strip():
        vb.append(f"Match Sample (intensity {st.session_state.match_intensity:.2f}):\n{st.session_state.voice_sample.strip()}")
    if st.session_state.vb_lock_on and st.session_state.voice_lock_prompt.strip():
        vb.append(f"VOICE LOCK (strength {st.session_state.lock_intensity:.2f}):\n{st.session_state.voice_lock_prompt.strip()}")
    voice_controls = "\n\n".join(vb).strip() if vb else "— None enabled —"

    exemplars: List[str] = []
    tv = st.session_state.trained_voice
    if st.session_state.vb_trained_on and tv and tv != "— None —":
        ctx = (st.session_state.main_text or "")[-2500:]
        query = ctx if ctx.strip() else st.session_state.synopsis
        exemplars = retrieve_mixed_exemplars(tv, lane, query)
    ex_block = "\n\n---\n\n".join(exemplars) if exemplars else "— None —"

    return f"""
YOU ARE OLIVETTI: the author's personal writing and editing partner.
Professional output only. No UI talk. No process talk.

STORY BIBLE IS CANON + IDEA BANK.
When generating NEW material, pull at least 2 concrete specifics from the Story Bible.

LANE: {lane}

VOICE CONTROLS:
{voice_controls}

TRAINED EXEMPLARS (mimic patterns, not content):
{ex_block}

STORY BIBLE:
{story_bible}

ACTION: {action_name}
""".strip()

def call_openai(system_brief: str, user_task: str, text: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK not installed. Add to requirements.txt: openai") from e

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_brief},
            {"role": "user", "content": f"{user_task}\n\nDRAFT:\n{text.strip()}"},
        ],
        temperature=0.75,
    )
    return (resp.choices[0].message.content or "").strip()

# ============================================================
# LOCAL TOOLS
# ============================================================
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

def local_find(text: str, query: str, limit: int = 12) -> List[Tuple[int, str]]:
    q = (query or "").strip()
    if not q:
        return []
    lines = (text or "").splitlines()
    hits = []
    for i, line in enumerate(lines, start=1):
        if q.lower() in line.lower():
            snippet = line.strip()
            if len(snippet) > 140:
                snippet = snippet[:140] + "…"
            hits.append((i, snippet))
            if len(hits) >= limit:
                break
    return hits

# ============================================================
# COMMANDS (Junk Drawer) - minimal but useful
# ============================================================
CMD_STATUS = re.compile(r"^\s*/status\s*$", re.IGNORECASE)
CMD_CLEAR  = re.compile(r"^\s*/clear\s*$", re.IGNORECASE)
CMD_FIND   = re.compile(r"^\s*/find\s*:\s*(.+)$", re.IGNORECASE)

CMD_CREATE = re.compile(r"^\s*/create\s*:\s*(.+)$", re.IGNORECASE)   # create project in NEW
CMD_PROMOTE = re.compile(r"^\s*/promote\s*$", re.IGNORECASE)         # promote current to next bay

CMD_SAVEVOICE = re.compile(r"^\s*/savevoice\s+(.+)$", re.IGNORECASE)
CMD_DELETEVOICE = re.compile(r"^\s*/deletevoice\s+(.+)$", re.IGNORECASE)
CMD_LISTVOICES = re.compile(r"^\s*/listvoices\s*$", re.IGNORECASE)

def next_bay(bay: str) -> Optional[str]:
    if bay == "NEW": return "ROUGH"
    if bay == "ROUGH": return "EDIT"
    if bay == "EDIT": return "FINAL"
    return None

def handle_junk_commands():
    raw = (st.session_state.junk or "").strip()
    if not raw:
        return

    if CMD_CLEAR.match(raw):
        st.session_state.junk = ""
        st.session_state.tool_output = ""
        st.session_state.voice_status = "Cleared."
        save_all_to_disk(force=True)
        return

    if CMD_STATUS.match(raw):
        bay = st.session_state.active_bay
        pid = st.session_state.project_id
        title = st.session_state.project_title
        counts = {b: len(list_projects_in_bay(b)) for b in BAYS}
        st.session_state.tool_output = (
            f"ACTIVE BAY: {bay}\n"
            f"ACTIVE PROJECT: {title} ({pid})\n\n"
            f"PROJECT COUNTS:\n" + "\n".join([f"- {b}: {counts[b]}" for b in BAYS])
        )
        st.session_state.voice_status = "Status."
        st.session_state.junk = ""
        return

    m = CMD_CREATE.match(raw)
    if m:
        title = m.group(1).strip()
        # only meaningful in NEW; but we’ll still create in NEW regardless
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

handle_junk_commands()

def handle_voice_sample_commands():
    raw = st.session_state.voice_sample or ""
    if not raw.strip():
        return
    lines = raw.splitlines()
    first = lines[0].strip()

    if CMD_LISTVOICES.match(first):
        names = sorted(st.session_state.voices.keys())
        st.session_state.tool_output = "VOICES:\n" + ("\n".join(names) if names else "— none —")
        st.session_state.voice_status = "Listed voices."
        st.session_state.voice_sample = ""
        autosave()
        return

    m = CMD_DELETEVOICE.match(first)
    if m:
        name = m.group(1).strip()
        msg = delete_voice(name)
        st.session_state.voice_status = msg
        st.session_state.tool_output = msg
        st.session_state.voice_sample = ""
        autosave()
        return

    m = CMD_SAVEVOICE.match(first)
    if m:
        name = m.group(1).strip()
        sample = "\n".join(lines[1:]).strip()
        if len(sample) < 200:
            st.session_state.voice_status = "Paste at least ~200 characters under /savevoice Name."
            st.session_state.tool_output = st.session_state.voice_status
            st.session_state.voice_sample = ""
            return
        imported, counts = import_samples_to_voice(name, sample)
        msg = f"Imported → {name}: {imported} chunks | " + " • ".join([f"{k}={v}" for k, v in counts.items()])
        st.session_state.voice_status = msg
        st.session_state.tool_output = msg
        st.session_state.voice_sample = ""
        autosave()
        return

handle_voice_sample_commands()

# ============================================================
# PARTNER ACTIONS (kept; no removals)
# ============================================================
def partner_action(action: str):
    text = st.session_state.main_text or ""
    lane = current_lane_from_draft(text)
    brief = build_partner_brief(action, lane=lane)
    use_ai = bool(OPENAI_API_KEY)

    def apply_replace(result: str):
        if result and result.strip():
            st.session_state.main_text = result.strip()
            st.session_state.last_action = action
            autosave()

    def apply_append(result: str):
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
            else:
                apply_replace(text)
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
            else:
                apply_replace(text)
            return

        if action == "Rephrase":
            if use_ai:
                task = f"Replace the final sentence with a stronger one (same meaning) in lane ({lane}). Return full text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action == "Describe":
            if use_ai:
                task = f"Add vivid controlled description in lane ({lane}). Preserve pace and canon. Return full revised text."
                out = call_openai(brief, task, text)
                apply_replace(out)
            else:
                apply_replace(text)
            return

        if action in ("Spell", "Grammar"):
            cleaned = local_cleanup(text)
            if use_ai:
                task = f"Copyedit spelling/grammar/punctuation. Preserve voice. Return full revised text."
                out = call_openai(brief, task, cleaned)
                apply_replace(out if out else cleaned)
            else:
                apply_replace(cleaned)
            return

        if action == "Find":
            m = CMD_FIND.match((st.session_state.junk or "").strip())
            query = m.group(1).strip() if m else ""
            if not query:
                st.session_state.tool_output = "Find: type /find: term in Junk Drawer."
                st.session_state.voice_status = "Find: waiting for query."
                autosave()
                return
            hits = local_find(text, query)
            if hits:
                st.session_state.tool_output = "FIND:\n" + "\n".join([f"Line {ln}: {snip}" for ln, snip in hits])
                st.session_state.voice_status = f"Find: {len(hits)} hit(s)."
            else:
                st.session_state.tool_output = "FIND:\nNo hits."
                st.session_state.voice_status = "Find: 0 hits."
            autosave()
            return

        apply_replace(text)

    except Exception as e:
        st.session_state.voice_status = f"Engine: {e}"
        st.session_state.tool_output = f"ERROR:\n{e}"
        autosave()

# ============================================================
# TOP BAR (buttons unchanged; now select WORK BAYS)
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
            <br/>Status: {st.session_state.voice_status}
        </div>
        """,
        unsafe_allow_html=True
    )

st.divider()

# ============================================================
# LOCKED LAYOUT (same ratios)
# ============================================================
left, center, right = st.columns([1.2, 3.2, 1.6])

# ============================================================
# LEFT — STORY BIBLE (now includes per-bay project selector + promote)
# ============================================================
with left:
    st.subheader("📖 Story Bible")

    # Project selector for current bay (minimal addition; lives in Story Bible, not top bar)
    bay = st.session_state.active_bay
    bay_projects = list_projects_in_bay(bay)
    labels = ["— (none) —"] + [f"{title}" for _, title in bay_projects]
    ids = [None] + [pid for pid, _ in bay_projects]

    current_pid = st.session_state.project_id if (st.session_state.project_id in ids) else None
    current_idx = ids.index(current_pid) if current_pid in ids else 0

    sel = st.selectbox("Current Bay Project", labels, index=current_idx, key="bay_project_selector")
    sel_pid = ids[labels.index(sel)] if sel in labels else None

    if sel_pid and sel_pid != st.session_state.project_id:
        save_session_into_project()
        st.session_state.active_project_by_bay[bay] = sel_pid
        load_project_into_session(sel_pid)
        st.session_state.voice_status = f"{bay}: {st.session_state.project_title}"
        st.session_state.last_action = "Select Project"
        autosave()

    # Bay actions
    action_cols = st.columns([1, 1])
    if bay == "NEW":
        # Create a new project in NEW from current Bible/Draft
        if action_cols[0].button("Create Project (from Bible)", key="create_project_btn"):
            # title = synopsis first line fallback
            title_guess = (st.session_state.synopsis.strip().splitlines()[0].strip() if st.session_state.synopsis.strip() else "New Project")
            pid = create_project_from_current_bible(title_guess)
            load_project_into_session(pid)
            st.session_state.voice_status = f"Created in NEW: {st.session_state.project_title}"
            st.session_state.last_action = "Create Project"
            autosave()

        # Promote NEW -> ROUGH
        if action_cols[1].button("Promote → Rough", key="promote_new_to_rough"):
            if st.session_state.project_id:
                save_session_into_project()
                promote_project(st.session_state.project_id, "ROUGH")
                st.session_state.active_project_by_bay["ROUGH"] = st.session_state.project_id
                switch_bay("ROUGH")
                st.session_state.voice_status = f"Promoted → ROUGH: {st.session_state.project_title}"
                st.session_state.last_action = "Promote → ROUGH"
                autosave()
    elif bay in ("ROUGH", "EDIT"):
        nb = next_bay(bay)
        if action_cols[1].button(f"Promote → {nb.title()}", key=f"promote_{bay.lower()}"):
            if st.session_state.project_id and nb:
                save_session_into_project()
                promote_project(st.session_state.project_id, nb)
                st.session_state.active_project_by_bay[nb] = st.session_state.project_id
                switch_bay(nb)
                st.session_state.voice_status = f"Promoted → {nb}: {st.session_state.project_title}"
                st.session_state.last_action = f"Promote → {nb}"
                autosave()

    with st.expander("🗃 Junk Drawer"):
        st.text_area("", key="junk", height=80, on_change=autosave,
                     help="Commands: /create: Title  |  /promote  |  /status  |  /find: term")
        st.text_area("Tool Output", key="tool_output", height=140, disabled=True)

    with st.expander("📝 Synopsis"):
        st.text_area("", key="synopsis", height=100, on_change=autosave)

    with st.expander("🎭 Genre / Style Notes"):
        st.text_area("", key="genre_style_notes", height=80, on_change=autosave)

    with st.expander("🌍 World Elements"):
        st.text_area("", key="world", height=100, on_change=autosave)

    with st.expander("👤 Characters"):
        st.text_area("", key="characters", height=120, on_change=autosave)

    with st.expander("🧱 Outline"):
        st.text_area("", key="outline", height=160, on_change=autosave)

# ============================================================
# CENTER — WRITING DESK (freewriting only)
# ============================================================
with center:
    st.subheader("✍️ Writing Desk")
    st.text_area("", key="main_text", height=650, on_change=autosave)

    b1 = st.columns(5)
    if b1[0].button("Write", key="btn_write"): partner_action("Write")
    if b1[1].button("Rewrite", key="btn_rewrite"): partner_action("Rewrite")
    if b1[2].button("Expand", key="btn_expand"): partner_action("Expand")
    if b1[3].button("Rephrase", key="btn_rephrase"): partner_action("Rephrase")
    if b1[4].button("Describe", key="btn_describe"): partner_action("Describe")

    b2 = st.columns(5)
    if b2[0].button("Spell", key="btn_spell"): partner_action("Spell")
    if b2[1].button("Grammar", key="btn_grammar"): partner_action("Grammar")
    if b2[2].button("Find", key="btn_find"): partner_action("Find")
    if b2[3].button("Synonym", key="btn_synonym"): partner_action("Synonym")
    if b2[4].button("Sentence", key="btn_sentence"): partner_action("Sentence")

# ============================================================
# RIGHT — VOICE BIBLE (unchanged structure)
# ============================================================
with right:
    st.subheader("🎙 Voice Bible")

    st.checkbox("Enable Writing Style", key="vb_style_on", on_change=autosave)
    st.selectbox(
        "Writing Style",
        ["Neutral", "Minimal", "Expressive", "Hardboiled", "Poetic"],
        key="writing_style",
        disabled=not st.session_state.vb_style_on,
        on_change=autosave
    )
    st.slider("Style Intensity", 0.0, 1.0, key="style_intensity",
              disabled=not st.session_state.vb_style_on, on_change=autosave)

    st.divider()

    st.checkbox("Enable Genre Influence", key="vb_genre_on", on_change=autosave)
    st.selectbox(
        "Genre",
        ["Literary", "Noir", "Thriller", "Comedy", "Lyrical"],
        key="genre",
        disabled=not st.session_state.vb_genre_on,
        on_change=autosave
    )
    st.slider("Genre Intensity", 0.0, 1.0, key="genre_intensity",
              disabled=not st.session_state.vb_genre_on, on_change=autosave)

    st.divider()

    st.checkbox("Enable Trained Voice", key="vb_trained_on", on_change=autosave)
    trained_options = voice_names_for_selector()
    if st.session_state.trained_voice not in trained_options:
        st.session_state.trained_voice = "— None —"
    st.selectbox("Trained Voice", trained_options, key="trained_voice",
                 disabled=not st.session_state.vb_trained_on, on_change=autosave)
    st.slider("Trained Voice Intensity", 0.0, 1.0, key="trained_intensity",
              disabled=not st.session_state.vb_trained_on, on_change=autosave)

    st.divider()

    st.checkbox("Enable Match My Style", key="vb_match_on", on_change=autosave)
    st.text_area(
        "Style Example",
        key="voice_sample",
        height=100,
        disabled=not st.session_state.vb_match_on,
        help="Import voice: first line '/savevoice Name' then paste pages. Also: /listvoices, /deletevoice Name.",
        on_change=autosave
    )
    st.slider("Match Intensity", 0.0, 1.0, key="match_intensity",
              disabled=not st.session_state.vb_match_on, on_change=autosave)

    st.divider()

    st.checkbox("Voice Lock (Hard Constraint)", key="vb_lock_on", on_change=autosave)
    st.text_area("Voice Lock Prompt", key="voice_lock_prompt", height=80,
                 disabled=not st.session_state.vb_lock_on, on_change=autosave)
    st.slider("Lock Strength", 0.0, 1.0, key="lock_intensity",
              disabled=not st.session_state.vb_lock_on, on_change=autosave)

    st.divider()

    st.selectbox("POV", ["First", "Close Third", "Omniscient"], key="pov", on_change=autosave)
    st.selectbox("Tense", ["Past", "Present"], key="tense", on_change=autosave)

# ============================================================
# SAFETY NET SAVE EVERY RERUN
# ============================================================
save_all_to_disk()

