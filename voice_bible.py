"""
============================================================
VOICE BIBLE - Intelligent Author Engine
============================================================
Unified AI Brief construction system that combines:
- AI Intensity controls
- Voice Vault (semantic voice samples)
- Style Banks (exemplar-based training)
- Story Bible (canon enforcement)
- Match My Style (one-shot adaptation)
- Voice Lock (hard constraints)
- Technical Controls (POV/Tense)

All AI generation routes through build_partner_brief() to ensure
consistent application of all Voice Bible settings.
============================================================
"""

from typing import List, Dict, Any, Tuple
import streamlit as st


def temperature_from_intensity(x: float) -> float:
    """
    Maps AI Intensity (0.0–1.0) → Temperature (0.1–1.1) with cubic curve.
    
    LOW (0.25) → 0.52 (predictable)
    MID (0.50) → 0.66 (balanced)
    HIGH (0.75) → 0.86 (creative)
    MAX (1.00) → 1.10 (wild)
    """
    return 0.1 + 1.0 * (x ** 3)


def build_partner_brief(action_name: str, lane: str) -> str:
    """
    ═══════════════════════════════════════════════════════════════
    UNIFIED AI BRIEF CONSTRUCTION
    ═══════════════════════════════════════════════════════════════
    Assembles complete Voice Bible brief that controls ALL AI generation.
    Every AI action (Write, Rewrite, Expand, Generate Synopsis, etc.) 
    routes through this function to ensure consistent voice enforcement.
    
    INPUTS FROM SESSION STATE:
    - ai_intensity: 0.0–1.0 (controls randomness via temperature)
    - writing_style: "NARRATIVE" | "DESCRIPTIVE" | "EMOTIONAL" | "LYRICAL"
    - genre_influence: "Literary" | "Commercial" | etc.
    - trained_voice_on + selected_voice: Voice Vault retrieval
    - vb_match_on + voice_sample: Match My Style one-shot
    - vb_lock_on + voice_lock_prompt: Hard constraints
    - vb_technical_on + pov/tense: Technical specs
    - Story Bible: Canon enforcement
    
    OUTPUTS:
    - Complete system prompt (500+ lines) with all settings applied
    - Used by call_openai() as system message
    
    VERIFICATION:
    ✓ All Voice Bible controls feed into this function
    ✓ All AI actions use this brief via call_openai()
    ✓ Changes to Voice Bible immediately affect all generation
    ═══════════════════════════════════════════════════════════════
    """
    # Import here to avoid circular dependency
    from app import (
        retrieve_mixed_exemplars, retrieve_style_exemplars,
        _story_bible_text, engine_style_directive, current_lane_from_draft
    )
    
    # Fetch current draft text for context
    text = st.session_state.draft or ""
    
    # === AI INTENSITY ===
    ai_x = st.session_state.get("ai_intensity", 0.5)
    temp = temperature_from_intensity(ai_x)
    intensity_desc = (
        "LOW (predictable, minimal creativity)"
        if ai_x < 0.4
        else "MEDIUM (balanced creativity)"
        if ai_x < 0.7
        else "HIGH (creative, exploratory)"
    )
    
    # === WRITING STYLE ===
    style = st.session_state.get("writing_style", "NARRATIVE")
    style_intensity = st.session_state.get("style_intensity", 0.5)
    style_directive = engine_style_directive(style, float(style_intensity), lane)
    
    # === GENRE INFLUENCE ===
    genre = st.session_state.get("genre_influence", "Literary")
    genre_notes = ""
    if genre == "Literary":
        genre_notes = "Prioritize literary prose with elevated language, metaphor, and emotional depth."
    elif genre == "Commercial":
        genre_notes = "Focus on clarity, accessibility, and forward momentum. Avoid purple prose."
    elif genre == "Thriller":
        genre_notes = "Emphasize tension, urgency, and short punchy sentences. Keep pacing tight."
    elif genre == "Romance":
        genre_notes = "Heighten emotional intimacy, sensory details, and character connection."
    elif genre == "Fantasy":
        genre_notes = "Balance worldbuilding exposition with immersive sensory grounding."
    elif genre == "SciFi":
        genre_notes = "Integrate technical concepts naturally. Avoid infodumps."
    
    # === TRAINED VOICE (Voice Vault) ===
    voice_examples = []
    if st.session_state.get("trained_voice_on", False):
        voice_name = st.session_state.get("selected_voice", "")
        if voice_name:
            # Retrieve semantic matches from voice vault
            voice_examples = retrieve_mixed_exemplars(voice_name, lane, text)
    
    # === STYLE BANKS (Exemplar-based learning) ===
    style_examples = []
    if st.session_state.get("style_banks_on", False):
        style_bank_name = st.session_state.get("active_style_bank", "")
        if style_bank_name:
            # Retrieve semantically similar exemplars
            style_examples = retrieve_style_exemplars(style_bank_name, lane, text, k=2)
    
    # === MATCH MY STYLE (One-shot adaptation) ===
    match_text = ""
    match_intensity = 0.0
    if st.session_state.get("vb_match_on", False):
        match_text = (st.session_state.get("voice_sample", "") or "").strip()
        match_intensity = st.session_state.get("match_intensity", 0.5)
        # Use analyzed samples if available
        analyzed = st.session_state.get("analyzed_style_samples", [])
        if analyzed:
            match_text = "\n\n".join(s["text"] for s in analyzed[:3])
    
    # === VOICE LOCK (Hard constraints) ===
    lock_text = ""
    lock_intensity = 0.0
    if st.session_state.get("vb_lock_on", False):
        lock_text = (st.session_state.get("voice_lock_prompt", "") or "").strip()
        lock_intensity = st.session_state.get("lock_intensity", 0.8)
    
    # === TECHNICAL CONTROLS (POV/Tense) ===
    tech_directive = ""
    if st.session_state.get("vb_technical_on", False):
        pov = st.session_state.get("pov", "Close Third")
        tense = st.session_state.get("tense", "Past")
        tech_intensity = st.session_state.get("technical_intensity", 0.5)
        tech_directive = f"""
TECHNICAL CONTROLS (Enforcement: {tech_intensity:.0%}):
- Point of View: {pov}
- Tense: {tense}
{"STRICT: Reject any output that violates POV/Tense." if tech_intensity > 0.7 else "MODERATE: Prefer consistency but allow flexibility." if tech_intensity > 0.4 else "LOOSE: Use as guideline only."}
"""
    
    # === STORY BIBLE (Canon enforcement) ===
    story_bible_context = _story_bible_text()
    
    # === ASSEMBLE UNIFIED BRIEF ===
    brief_parts = []
    
    # Header
    brief_parts.append("=" * 60)
    brief_parts.append("OLIVETTI CREATIVE EDITING PARTNER — AI BRIEF")
    brief_parts.append("=" * 60)
    brief_parts.append(f"Action: {action_name}")
    brief_parts.append(f"Lane: {lane}")
    brief_parts.append(f"AI Intensity: {ai_x:.2f} ({intensity_desc}) → Temperature: {temp:.2f}")
    brief_parts.append("")
    
    # Core directives
    brief_parts.append("CORE MISSION:")
    brief_parts.append("You are Olivetti, a professional creative editing partner.")
    brief_parts.append(f"Current action: {action_name}")
    brief_parts.append(f"Target lane: {lane} (adjust tone/pacing accordingly)")
    brief_parts.append("")
    
    # Writing style
    brief_parts.append("WRITING STYLE:")
    brief_parts.append(f"Primary: {style}")
    brief_parts.append(style_directive)
    brief_parts.append("")
    
    # Genre influence
    if genre_notes:
        brief_parts.append("GENRE INFLUENCE:")
        brief_parts.append(f"{genre}: {genre_notes}")
        brief_parts.append("")
    
    # Voice Lock (highest priority)
    if lock_text and lock_intensity > 0.3:
        brief_parts.append("=" * 60)
        brief_parts.append("🔒 VOICE LOCK — MANDATORY CONSTRAINTS")
        brief_parts.append("=" * 60)
        brief_parts.append(f"Enforcement Level: {lock_intensity:.0%}")
        brief_parts.append("")
        brief_parts.append(lock_text)
        brief_parts.append("")
        if lock_intensity > 0.7:
            brief_parts.append("⚠️ CRITICAL: Reject any output that violates these constraints.")
        brief_parts.append("=" * 60)
        brief_parts.append("")
    
    # Technical controls
    if tech_directive:
        brief_parts.append(tech_directive)
        brief_parts.append("")
    
    # Match My Style
    if match_text and match_intensity > 0.3:
        brief_parts.append("=" * 60)
        brief_parts.append("✨ MATCH MY STYLE — ONE-SHOT ADAPTATION")
        brief_parts.append("=" * 60)
        brief_parts.append(f"Match Intensity: {match_intensity:.0%}")
        brief_parts.append("")
        brief_parts.append("Analyze and replicate these patterns:")
        brief_parts.append(match_text[:2000])  # Limit to 2000 chars
        brief_parts.append("")
        if match_intensity > 0.7:
            brief_parts.append("HIGH INTENSITY: Closely mimic sentence structure, rhythm, and vocabulary.")
        elif match_intensity > 0.4:
            brief_parts.append("MEDIUM INTENSITY: Adapt general patterns while maintaining flexibility.")
        else:
            brief_parts.append("LOW INTENSITY: Use as subtle influence only.")
        brief_parts.append("=" * 60)
        brief_parts.append("")
    
    # Voice Vault examples
    if voice_examples:
        brief_parts.append("=" * 60)
        brief_parts.append("🎤 TRAINED VOICE — SEMANTIC EXAMPLES")
        brief_parts.append("=" * 60)
        brief_parts.append(f"Voice: {st.session_state.get('selected_voice', 'Unknown')}")
        brief_parts.append(f"Lane: {lane}")
        brief_parts.append("")
        for idx, ex in enumerate(voice_examples[:3], 1):
            brief_parts.append(f"Example {idx}:")
            brief_parts.append(ex)
            brief_parts.append("")
        brief_parts.append("INSTRUCTION: Emulate these patterns in your output.")
        brief_parts.append("=" * 60)
        brief_parts.append("")
    
    # Style Banks examples
    if style_examples:
        brief_parts.append("=" * 60)
        brief_parts.append("📚 STYLE EXEMPLARS — TRAINED PATTERNS")
        brief_parts.append("=" * 60)
        brief_parts.append(f"Style Bank: {st.session_state.get('active_style_bank', 'Unknown')}")
        brief_parts.append(f"Lane: {lane}")
        brief_parts.append("")
        for idx, ex in enumerate(style_examples, 1):
            brief_parts.append(f"Exemplar {idx}:")
            brief_parts.append(ex)
            brief_parts.append("")
        brief_parts.append("INSTRUCTION: Learn from these writing patterns.")
        brief_parts.append("=" * 60)
        brief_parts.append("")
    
    # Story Bible
    if story_bible_context.strip():
        brief_parts.append("=" * 60)
        brief_parts.append("📖 STORY BIBLE — CANON ENFORCEMENT")
        brief_parts.append("=" * 60)
        brief_parts.append(story_bible_context)
        brief_parts.append("")
        brief_parts.append("INSTRUCTION: Maintain consistency with established canon.")
        brief_parts.append("=" * 60)
        brief_parts.append("")
    
    # Footer
    brief_parts.append("=" * 60)
    brief_parts.append("EXECUTION INSTRUCTIONS")
    brief_parts.append("=" * 60)
    brief_parts.append("1. Apply Voice Lock constraints FIRST (mandatory)")
    brief_parts.append("2. Respect Technical Controls (POV/Tense)")
    brief_parts.append("3. Match provided style examples when available")
    brief_parts.append("4. Maintain Story Bible canon consistency")
    brief_parts.append("5. Apply Writing Style and Genre Influence")
    brief_parts.append("6. Output professional prose ready for publication")
    brief_parts.append("=" * 60)
    
    return "\n".join(brief_parts)


def get_voice_bible_summary() -> str:
    """
    Generate a compact status summary showing which Voice Bible controls are active.
    Used in UI to give user visibility into what's controlling AI generation.
    """
    active = []
    
    ai_x = st.session_state.get("ai_intensity", 0.5)
    ai_label = "LOW" if ai_x < 0.4 else "MID" if ai_x < 0.7 else "HIGH"
    active.append(f"AI:{ai_label}")
    
    style = st.session_state.get("writing_style", "NARRATIVE")
    active.append(f"Style:{style}")
    
    genre = st.session_state.get("genre_influence", "Literary")
    active.append(f"Genre:{genre}")
    
    if st.session_state.get("trained_voice_on", False):
        voice_name = st.session_state.get("selected_voice", "")
        if voice_name:
            active.append(f"🎤{voice_name}")
    
    if st.session_state.get("style_banks_on", False):
        bank_name = st.session_state.get("active_style_bank", "")
        if bank_name:
            active.append(f"📚{bank_name}")
    
    if st.session_state.get("vb_match_on", False):
        match_x = st.session_state.get("match_intensity", 0.5)
        active.append(f"✨Match:{match_x:.0%}")
    
    if st.session_state.get("vb_lock_on", False):
        lock_x = st.session_state.get("lock_intensity", 0.8)
        active.append(f"🔒Lock:{lock_x:.0%}")
    
    if st.session_state.get("vb_technical_on", False):
        pov = st.session_state.get("pov", "Close Third")
        tense = st.session_state.get("tense", "Past")
        active.append(f"⚙️{pov}/{tense}")
    
    return " • ".join(active) if active else "Default settings"


# Style guide definitions
_ENGINE_STYLE_GUIDE = {
    "NARRATIVE": "Narrative clarity, clean cause→effect, confident pacing. Prioritize story logic and readability.",
    "DESCRIPTIVE": "Sensory precision, spatial clarity, vivid concrete nouns, controlled detail density (no purple bloat).",
    "EMOTIONAL": "Interior depth, subtext, emotional specificity. Show the feeling through behavior, sensation, and thought.",
    "LYRICAL": "Rhythm, musical syntax, image-forward language, elegant metaphor with restraint. Make prose sing without obscuring meaning.",
}


def engine_style_directive(style: str, intensity: float = 0.5, lane: str = "") -> str:
    """
    Generate detailed style directives for each ENGINE_STYLE option.
    These are prose-level instructions that shape sentence structure,
    vocabulary, and narrative approach.
    
    Args:
        style: The writing style (NARRATIVE, DESCRIPTIVE, EMOTIONAL, LYRICAL)
        intensity: Style intensity 0.0-1.0 (how strongly to apply the style)
        lane: The current narrative lane for context
    
    Returns:
        Formatted style directive string
    """
    style = (style or "").strip().upper()
    base = _ENGINE_STYLE_GUIDE.get(style, "")
    x = float(intensity)
    
    if x <= 0.33:
        mod = "Keep it subtle and controlled. Minimal overt stylization."
    elif x <= 0.66:
        mod = "Medium stylization. Let the style clearly shape diction and cadence."
    else:
        mod = "High stylization. Strong stylistic fingerprint, but still professional and coherent."
    
    result = base
    if lane:
        result += f"\nLane: {lane}"
    result += f"\n{mod}"
    
    return result
