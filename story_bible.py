"""
============================================================
STORY BIBLE - Canon Management & Project Model
============================================================
Manages story world information, characters, outline, and metadata.
Provides canon context to AI generation for consistency.
============================================================
"""

from typing import Dict, Any
import hashlib
from datetime import datetime
import streamlit as st


def now_ts() -> str:
    """Current timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def _fingerprint_story_bible(sb: Dict[str, str]) -> str:
    """
    Generate a content fingerprint for story bible change detection.
    Used to track when story bible has been modified.
    """
    parts = [
        (sb.get("synopsis", "") or "").strip(),
        (sb.get("genre_style_notes", "") or "").strip(),
        (sb.get("world", "") or "").strip(),
        (sb.get("characters", "") or "").strip(),
        (sb.get("outline", "") or "").strip(),
    ]
    combined = "|".join(parts)
    return hashlib.md5(combined.encode("utf-8")).hexdigest()[:12]


def default_story_bible_workspace() -> Dict[str, Any]:
    """
    Create a new empty story bible workspace structure.
    """
    ts = now_ts()
    return {
        "workspace_story_bible_id": hashlib.md5(f"wsb|{ts}".encode("utf-8")).hexdigest()[:12],
        "workspace_story_bible_created_ts": ts,
        "title": "",
        "draft": "",
        "story_bible": {
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        },
        "story_bible_updated_ts": ts,
        "story_bible_fingerprint": _fingerprint_story_bible({
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        }),
    }


def get_story_bible_text() -> str:
    """
    Assemble story bible context from active project or workspace.
    Returns formatted text for inclusion in AI briefs.
    """
    # Determine if in workspace mode or project mode
    if st.session_state.get("in_workspace_mode", False):
        sb = st.session_state.get("story_bible", {})
    else:
        # Get from active project
        bay = st.session_state.get("active_bay", "NEW")
        proj_id = st.session_state.get("active_project_by_bay", {}).get(bay)
        if not proj_id or "projects" not in st.session_state:
            return ""
        
        proj = st.session_state.projects.get(proj_id)
        if not proj:
            return ""
        
        sb = proj.get("story_bible", {})
    
    if not sb:
        return ""
    
    # Format story bible sections
    sections = []
    
    synopsis = (sb.get("synopsis", "") or "").strip()
    if synopsis:
        sections.append("SYNOPSIS:\n" + synopsis)
    
    genre = (sb.get("genre_style_notes", "") or "").strip()
    if genre:
        sections.append("GENRE & STYLE:\n" + genre)
    
    world = (sb.get("world", "") or "").strip()
    if world:
        sections.append("WORLD:\n" + world)
    
    chars = (sb.get("characters", "") or "").strip()
    if chars:
        sections.append("CHARACTERS:\n" + chars)
    
    outline = (sb.get("outline", "") or "").strip()
    if outline:
        sections.append("OUTLINE:\n" + outline)
    
    if not sections:
        return ""
    
    return "\n\n".join(sections)


def update_story_bible_section(section_key: str, content: str) -> None:
    """
    Update a specific story bible section and update fingerprint.
    
    Args:
        section_key: One of ["synopsis", "genre_style_notes", "world", "characters", "outline"]
        content: New content for the section
    """
    if st.session_state.get("in_workspace_mode", False):
        # Update workspace story bible
        if "story_bible" not in st.session_state:
            st.session_state.story_bible = {}
        
        st.session_state.story_bible[section_key] = content
        st.session_state.story_bible_updated_ts = now_ts()
        st.session_state.story_bible_fingerprint = _fingerprint_story_bible(st.session_state.story_bible)
    else:
        # Update active project story bible
        bay = st.session_state.get("active_bay", "NEW")
        proj_id = st.session_state.get("active_project_by_bay", {}).get(bay)
        
        if proj_id and "projects" in st.session_state:
            proj = st.session_state.projects.get(proj_id)
            if proj:
                if "story_bible" not in proj:
                    proj["story_bible"] = {}
                
                proj["story_bible"][section_key] = content
                proj["story_bible_updated_ts"] = now_ts()
                proj["story_bible_fingerprint"] = _fingerprint_story_bible(proj["story_bible"])


def story_bible_markdown(title: str, sb: Dict[str, str], meta: Dict[str, Any]) -> str:
    """
    Generate markdown export of story bible.
    
    Returns:
        Formatted markdown string
    """
    lines = []
    lines.append(f"# Story Bible: {title}")
    lines.append("")
    lines.append(f"*Created: {meta.get('story_bible_created_ts', 'Unknown')}*")
    lines.append(f"*Updated: {meta.get('story_bible_updated_ts', 'Unknown')}*")
    lines.append("")
    
    sections = [
        ("Synopsis", "synopsis"),
        ("Genre & Style Notes", "genre_style_notes"),
        ("World", "world"),
        ("Characters", "characters"),
        ("Outline", "outline"),
    ]
    
    for section_title, section_key in sections:
        content = (sb.get(section_key, "") or "").strip()
        if content:
            lines.append(f"## {section_title}")
            lines.append("")
            lines.append(content)
            lines.append("")
    
    return "\n".join(lines)


def create_project(title: str, bay: str) -> str:
    """
    Create a new project in the specified bay.
    
    Args:
        title: Project title
        bay: One of ["NEW", "ROUGH", "EDIT", "FINAL"]
    
    Returns:
        Project ID (hash)
    """
    if "projects" not in st.session_state:
        st.session_state.projects = {}
    
    ts = now_ts()
    proj_id = hashlib.md5(f"{title}|{ts}".encode("utf-8")).hexdigest()[:12]
    
    st.session_state.projects[proj_id] = {
        "id": proj_id,
        "title": title,
        "bay": bay,
        "draft": "",
        "story_bible": {
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        },
        "created_ts": ts,
        "updated_ts": ts,
        "story_bible_updated_ts": ts,
        "story_bible_fingerprint": _fingerprint_story_bible({
            "synopsis": "",
            "genre_style_notes": "",
            "world": "",
            "characters": "",
            "outline": "",
        }),
        "word_count": 0,
    }
    
    return proj_id


def list_projects_in_bay(bay: str) -> list:
    """
    Get list of all projects in a specific bay.
    
    Returns:
        List of project dicts sorted by updated_ts (most recent first)
    """
    if "projects" not in st.session_state:
        return []
    
    projects = [
        p for p in st.session_state.projects.values()
        if p.get("bay") == bay
    ]
    
    # Sort by updated_ts descending
    projects.sort(key=lambda p: p.get("updated_ts", ""), reverse=True)
    return projects


def move_project_to_bay(proj_id: str, new_bay: str) -> bool:
    """
    Move a project to a different bay.
    
    Returns:
        True if moved, False if project not found
    """
    if "projects" not in st.session_state:
        return False
    
    proj = st.session_state.projects.get(proj_id)
    if not proj:
        return False
    
    proj["bay"] = new_bay
    proj["updated_ts"] = now_ts()
    return True


def delete_project(proj_id: str) -> bool:
    """
    Delete a project.
    
    Returns:
        True if deleted, False if project not found
    """
    if "projects" not in st.session_state:
        return False
    
    if proj_id not in st.session_state.projects:
        return False
    
    del st.session_state.projects[proj_id]
    return True
