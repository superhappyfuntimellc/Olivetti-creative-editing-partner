from __future__ import annotations

import os
import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st
from openai import OpenAI

# -----------------------------
# Streamlit / env setup
# -----------------------------
os.environ["STREAMLIT_WATCH_FILES"] = "false"
client = OpenAI()

DEFAULT_MODEL = "gpt-5.2"

PROJECTS_DIR = Path("projects")
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# Helpers: storage
# -----------------------------
def _safe_slug(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"

def new_project_id(title: str) -> str:
    return f"{_safe_slug(title)[:32]}-{uuid.uuid4().hex[:8]}"

def project_dir(pid: str) -> Path:
    p = PROJECTS_DIR / pid
    p.mkdir(parents=True, exist_ok=True)
    return p

def read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def list_projects() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for p in PROJECTS_DIR.iterdir():
        if p.is_dir():
            meta = read_json(p / "meta.json", {"title": p.name})
            out[p.name] = meta
    return dict(sorted(out.items(), key=lambda kv: (kv[1].get("title", "") or "").lower()))

def load_project(pid: str) -> Dict[str, Any]:
    pdir = project_dir(pid)
    return {
        "meta": read_json(pdir / "meta.json", {"title": pid}),
        "story_bible": read_json(pdir / "story_bible.json", {}),
        "voice_bible": read_json(pdir / "voice_bible.json", {}),
        "doc": (pdir / "doc.txt").read_text(encoding="utf-8") if (pdir / "doc.txt").exists() else "",
        "settings": read_json(pdir / "settings.json", {}),
        "history": read_json(pdir / "history.json", []),
    }

def save_project(
    pid: str,
    *,
    meta=None,
    story_bible=None,
    voice_bible=None,
    doc=None,
    settings=None,
    history=None,
) -> None:
    pdir = project_dir(pid)
    if meta is not None:
        write_json(pdir / "meta.json", meta)
    if story_bible is not None:
        write_json(pdir / "story_bible.json", story_bible)
    if voice_bible is not None:
        write_json(pdir / "voice_bible.json", voice_bible)
    if doc is not None:
        (pdir / "doc.txt").write_text(doc, encoding="utf-8")
    if settings is not None:
        write_json(pdir / "settings.json", settings)
    if history is not None:
        write_json(pdir / "history.json", history)

# -----------------------------
# Helpers: AI
# -----------------------------
# -----------------------------
# Helpers: AI
# -----------------------------

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error(
            "Missing OPENAI_API_KEY. Add it in Streamlit Cloud → App → Settings → Secrets."
        )
        st.stop()
    try:
        return OpenAI(api_key=api_key)
    except Exception as exc:
        st.error(f"Unable to initialize OpenAI client: {exc}")
        st.stop()


def responses_text(
    *,
    model: str,
    instructions: str,
    input_text: str,
    max_output_tokens: int = 700,
) -> str:
    client = get_openai_client()
    resp = client.responses.create(
        model=model,
        instructions=instructions,
        input=input_text,  # ← THIS is the important line
        max_output_tokens=max_output_tokens,
    )
    return (resp.output_text or "").strip()


def responses_json(
    *,
    model: str,
    instructions: str,
    input_text: str,
    max_output_tokens: int = 900,
) -> dict:
    text = responses_text(
        model=model,
        instructions=instructions,
        input_text=input_text,
        max_output_tokens=max_output_tokens,
    )
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise

# -----------------------------
# Prompt building (Sudowrite-ish)
# -----------------------------
BASE_RULES = [
    "Preserve POV and tense from the provided scene.",
    "Match the existing prose voice and cadence.",
    "Do not introduce new named characters unless explicitly requested.",
    "Do not resolve major plot threads prematurely.",
    "Avoid clichés, filler, and vague phrasing. Be concrete and sensory.",
]

def build_instructions(voice_bible: Dict[str, Any], intensity: float) -> str:
    vb = voice_bible or {}
    style = vb.get("style_notes", "")
    do = vb.get("do", [])
    dont = vb.get("dont", [])
    lex = vb.get("lexicon", [])
    anti = vb.get("anti_lexicon", [])

    pov = vb.get("pov", "")
    tense = vb.get("tense", "")
    rhythm = vb.get("sentence_rhythm", "")
    imagery = vb.get("imagery_profile", "")
    dialogue = vb.get("dialogue_profile", "")
    metaphor_policy = vb.get("metaphor_policy", "")
    profanity_policy = vb.get("profanity_policy", "")

    return f"""
You are a production-grade fiction writing assistant.

CORE RULES (STRICT):
- {"\n- ".join(BASE_RULES)}

INTENSITY: {intensity:.2f}
- Lower intensity => minimal change, preserve phrasing, subtle improvements.
- Higher intensity => richer prose, stronger imagery, bolder language, still consistent.

VOICE BIBLE:
- POV: {pov}
- Tense: {tense}
- Sentence rhythm: {rhythm}
- Imagery profile: {imagery}
- Dialogue profile: {dialogue}
- Metaphor policy: {metaphor_policy}
- Profanity policy: {profanity_policy}
- Style notes: {style}
- Do: {do}
- Don't: {dont}
- Lexicon / motifs: {lex}
- Avoid: {anti}

Output only the requested content. No prefaces, no commentary.
""".strip()

def make_task_payload(action: str, story_bible: Dict[str, Any], scene: str, selection: str, extra: Dict[str, Any]) -> str:
    sb = story_bible or {}
    return f"""
ACTION:
{action}

STORY BIBLE:
World: {sb.get("world","")}
Outline / beats: {sb.get("outline","")}
Characters: {sb.get("characters","")}
Guardrails: {sb.get("guardrails","")}

CURRENT SCENE (context):
{scene}

USER SELECTION (may be empty):
{selection}

EXTRA:
{extra}
""".strip()

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

# -----------------------------
# App constants
# -----------------------------
ACTIONS = [
    ("Continue", "continue_scene", "Continue the scene for ~1–2 paragraphs without introducing new plot threads."),
    ("Rewrite", "rewrite_selection", "Rewrite the selection to improve flow and voice while preserving meaning."),
    ("Expand", "expand_sensory", "Expand the selection with sensory detail (tactile, smell, micro-actions)."),
    ("Describe", "describe_more", "Describe the moment more vividly (concrete imagery, specific nouns/verbs)."),
    ("Brainstorm", "brainstorm_next", "Brainstorm 6 strong next-beat options consistent with the outline."),
]

def default_settings() -> Dict[str, Any]:
    return {
        "model": DEFAULT_MODEL,
        "locked": False,
        "actions": {k: {"enabled": True, "intensity": 0.75} for _, k, _ in ACTIONS},
    }

def normalize_settings(s: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(s, dict) or not s:
        s = default_settings()
    if "model" not in s:
        s["model"] = DEFAULT_MODEL
    if "locked" not in s:
        s["locked"] = False
    if "actions" not in s or not isinstance(s["actions"], dict):
        s["actions"] = default_settings()["actions"]
    # Ensure all actions exist
    for _, k, _ in ACTIONS:
        if k not in s["actions"]:
            s["actions"][k] = {"enabled": True, "intensity": 0.75}
        if "enabled" not in s["actions"][k]:
            s["actions"][k]["enabled"] = True
        if "intensity" not in s["actions"][k]:
            s["actions"][k]["intensity"] = 0.75
    return s

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Sudowrite Clone (Clean + Auto Voice)", layout="wide")
st.title("Sudowrite Clone (Clean + Auto Voice Learning)")

# Sidebar: projects
st.sidebar.header("Projects")
projects = list_projects()

if "pid" not in st.session_state:
    st.session_state.pid = next(iter(projects.keys()), None)

with st.sidebar.expander("Create new project", expanded=False):
    new_title = st.text_input("Title", value="New Story")
    if st.button("Create Project"):
        pid_new = new_project_id(new_title)
        save_project(
            pid_new,
            meta={"title": new_title},
            story_bible={},
            voice_bible={},
            doc="",
            settings=default_settings(),
            history=[],
        )
        st.session_state.pid = pid_new
        st.rerun()

if not projects:
    st.info("Create a project to begin.")
    st.stop()

pid = st.sidebar.selectbox(
    "Open project",
    options=list(projects.keys()),
    format_func=lambda x: projects.get(x, {}).get("title", x),
    index=list(projects.keys()).index(st.session_state.pid) if st.session_state.pid in projects else 0,
)

data = load_project(pid)
meta = data["meta"]
story_bible = data["story_bible"]
voice_bible = data["voice_bible"]
doc = data["doc"]
history: List[Dict[str, Any]] = data["history"]
settings = normalize_settings(data["settings"])

st.sidebar.markdown("---")
settings["model"] = st.sidebar.text_input("Model", value=settings["model"])
settings["locked"] = st.sidebar.toggle("Lock AI button settings for this project", value=bool(settings["locked"]))

st.sidebar.markdown("### Button Controls")
for label, key, _desc in ACTIONS:
    with st.sidebar.expander(label, expanded=False):
        settings["actions"][key]["enabled"] = st.toggle(
            f"{label} enabled",
            value=bool(settings["actions"][key]["enabled"]),
            key=f"en_{pid}_{key}",
        )
        settings["actions"][key]["intensity"] = st.slider(
            f"{label} intensity",
            0.0,
            1.0,
            float(settings["actions"][key]["intensity"]),
            0.05,
            key=f"in_{pid}_{key}",
        )

# Save settings immediately
save_project(pid, settings=settings)

# Layout columns
left, center, right = st.columns([1.1, 2.2, 1.1])

with left:
    st.subheader(meta.get("title", pid))
    new_title2 = st.text_input("Project title", value=meta.get("title", pid))
    if st.button("Save title"):
        meta["title"] = new_title2
        save_project(pid, meta=meta)
        st.success("Saved.")
        st.rerun()

    st.markdown("---")
    st.subheader("Story Bible")
    story_bible["world"] = st.text_area("World", value=story_bible.get("world", ""), height=110)
    story_bible["outline"] = st.text_area("Outline / beats", value=story_bible.get("outline", ""), height=110)
    story_bible["guardrails"] = st.text_area("Guardrails (no-go rules)", value=story_bible.get("guardrails", ""), height=90)
    story_bible["characters"] = st.text_area(
        "Characters (freeform / JSON-ish ok)",
        value=str(story_bible.get("characters", "")),
        height=110,
    )
    if st.button("Save Story Bible"):
        save_project(pid, story_bible=story_bible)
        st.success("Saved.")

with center:
    st.subheader("Writing Desk")
    doc = st.text_area("Scene / Draft", value=doc, height=420)
    selection = st.text_area("Selection (paste highlighted text here)", value="", height=120)

    if "last_output" not in st.session_state:
        st.session_state.last_output = ""

    def run_action(label: str, key: str, description: str) -> None:
        if not settings["actions"][key]["enabled"]:
            st.warning(f"{label} is disabled for this project.")
            return

        intensity = float(settings["actions"][key]["intensity"])
        instructions = build_instructions(voice_bible, intensity=intensity)
        payload = make_task_payload(description, story_bible, scene=doc, selection=selection, extra={"project": meta.get("title", pid)})

        try:
            out = responses_text(model=settings["model"], instructions=instructions, input_text=payload, max_output_tokens=750)
        except Exception as e:
            st.error(f"AI error: {e}")
            return

        st.session_state.last_output = out
        history.append({"action": label, "selection": selection, "output": out})
        save_project(pid, doc=doc, history=history)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("Continue"):
            run_action("Continue", "continue_scene", ACTIONS[0][2])
    with c2:
        if st.button("Rewrite"):
            run_action("Rewrite", "rewrite_selection", ACTIONS[1][2])
    with c3:
        if st.button("Expand"):
            run_action("Expand", "expand_sensory", ACTIONS[2][2])
    with c4:
        if st.button("Describe"):
            run_action("Describe", "describe_more", ACTIONS[3][2])
    with c5:
        if st.button("Brainstorm"):
            run_action("Brainstorm", "brainstorm_next", ACTIONS[4][2])

    st.markdown("---")
    st.subheader("Output")
    out = st.text_area("AI Output", value=st.session_state.last_output, height=220)

    a, b, c = st.columns(3)
    with a:
        if st.button("Append output to draft"):
            if out.strip():
                doc2 = (doc.rstrip() + "\n\n" + out.strip() + "\n")
                save_project(pid, doc=doc2)
                st.success("Appended.")
                st.rerun()
    with b:
        if st.button("Save Draft"):
            save_project(pid, doc=doc)
            st.success("Saved.")
    with c:
        if st.button("Clear Output"):
            st.session_state.last_output = ""
            st.rerun()

    st.markdown("---")
    st.subheader("History (last 10)")
    if history:
        for h in reversed(history[-10:]):
            st.markdown(f"**{h.get('action','')}**")
            if (h.get("selection") or "").strip():
                st.code((h["selection"] or "")[:700])
            st.code((h.get("output", "") or "")[:1600])
    else:
        st.caption("No generations yet.")

with right:
    st.subheader("Voice Bible")
    voice_bible["style_notes"] = st.text_area("Style notes", value=voice_bible.get("style_notes", ""), height=120)

    # Keep these as newline lists
    def _as_lines(v) -> List[str]:
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        if isinstance(v, str):
            return [line for line in v.splitlines() if line.strip()]
        return []

    voice_bible["do"] = _as_lines(st.text_area("Do (one per line)", value="\n".join(_as_lines(voice_bible.get("do", []))), height=90))
    voice_bible["dont"] = _as_lines(st.text_area("Don't (one per line)", value="\n".join(_as_lines(voice_bible.get("dont", []))), height=90))
    voice_bible["lexicon"] = _as_lines(st.text_area("Lexicon / motifs (one per line)", value="\n".join(_as_lines(voice_bible.get("lexicon", []))), height=90))
    voice_bible["anti_lexicon"] = _as_lines(st.text_area("Avoid (one per line)", value="\n".join(_as_lines(voice_bible.get("anti_lexicon", []))), height=90))

    voice_bible["pov"] = st.text_input("POV (optional)", value=voice_bible.get("pov", ""))
    voice_bible["tense"] = st.text_input("Tense (optional)", value=voice_bible.get("tense", ""))
    voice_bible["sentence_rhythm"] = st.text_input("Sentence rhythm (optional)", value=voice_bible.get("sentence_rhythm", ""))
    voice_bible["imagery_profile"] = st.text_input("Imagery profile (optional)", value=voice_bible.get("imagery_profile", ""))
    voice_bible["dialogue_profile"] = st.text_input("Dialogue profile (optional)", value=voice_bible.get("dialogue_profile", ""))
    voice_bible["metaphor_policy"] = st.text_input("Metaphor policy (optional)", value=voice_bible.get("metaphor_policy", ""))
    voice_bible["profanity_policy"] = st.text_input("Profanity policy (optional)", value=voice_bible.get("profanity_policy", ""))

    if st.button("Save Voice Bible"):
        save_project(pid, voice_bible=voice_bible)
        st.success("Saved.")

    st.markdown("---")
    st.subheader("Auto Voice Learning")
    sample_len = st.slider("Use last N characters of draft", 2000, 20000, 8000, step=500)

    if st.button("Learn Voice from Draft"):
        sample = (doc or "")[-int(sample_len):]
        if len(sample.strip()) < 400:
            st.warning("Write a bit more first (need at least ~400 characters).")
        else:
            learn_instructions = "You are a precise literary style analyst. Output STRICT JSON only."
            payload = make_voice_learn_payload(sample)

            try:
                learned = responses_json(
                    model=settings["model"],
                    instructions=learn_instructions,
                    input_text=payload,
                    max_output_tokens=950,
                )
            except Exception as e:
                st.error(f"Voice learning error: {e}")
                st.stop()

            # Merge learned into voice_bible
            for k in [
                "style_notes", "pov", "tense", "sentence_rhythm", "imagery_profile",
                "dialogue_profile", "metaphor_policy", "profanity_policy"
            ]:
                v = learned.get(k)
                if isinstance(v, str) and v.strip():
                    voice_bible[k] = v.strip()

            for k in ["do", "dont", "lexicon", "anti_lexicon"]:
                v = learned.get(k)
                if isinstance(v, list):
                    voice_bible[k] = [str(x).strip() for x in v if str(x).strip()][:30]

            save_project(pid, voice_bible=voice_bible)
            st.success("Voice learned + saved to this project.")
            st.rerun()

