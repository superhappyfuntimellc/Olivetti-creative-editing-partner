"""
============================================================
STYLE BANKS - Exemplar-Based Writing Training
============================================================
Stores writing exemplars per lane and retrieves semantically
similar samples to guide AI generation.

Similar to Voice Vault but focused on stylistic patterns
rather than voice characteristics.
============================================================
"""

from typing import List, Dict, Any
import streamlit as st
from voice_vault import _simple_vec, _cosine_sim


def create_style_bank(bank_name: str) -> bool:
    """
    Create a new style bank.
    
    Returns:
        True if created, False if name already exists
    """
    if "style_banks" not in st.session_state:
        st.session_state.style_banks = {}
    
    if bank_name in st.session_state.style_banks:
        return False
    
    st.session_state.style_banks[bank_name] = {
        "Dialogue": [],
        "Narration": [],
        "Interiority": [],
        "Action": []
    }
    return True


def add_style_exemplar(bank_name: str, lane: str, exemplar_text: str) -> bool:
    """
    Add a style exemplar to the bank.
    
    Args:
        bank_name: Name of the style bank
        lane: One of ["Dialogue", "Narration", "Interiority", "Action"]
        exemplar_text: Writing exemplar
    
    Returns:
        True if added, False if exemplar_text is empty
    """
    if not exemplar_text or not exemplar_text.strip():
        return False
    
    if "style_banks" not in st.session_state:
        st.session_state.style_banks = {}
    
    if bank_name not in st.session_state.style_banks:
        create_style_bank(bank_name)
    
    exemplar_obj = {
        "text": exemplar_text.strip(),
        "vector": _simple_vec(exemplar_text.strip()),
        "word_count": len(exemplar_text.split())
    }
    
    st.session_state.style_banks[bank_name][lane].append(exemplar_obj)
    return True


def delete_style_exemplar(bank_name: str, lane: str, index_from_end: int = 0) -> bool:
    """
    Delete a style exemplar (default: most recent).
    
    Returns:
        True if deleted, False if none available
    """
    if "style_banks" not in st.session_state:
        return False
    
    if bank_name not in st.session_state.style_banks:
        return False
    
    exemplars = st.session_state.style_banks[bank_name].get(lane, [])
    if not exemplars or index_from_end >= len(exemplars):
        return False
    
    del exemplars[-(index_from_end + 1)]
    return True


def retrieve_style_exemplars(style_bank: str, lane: str, query: str, k: int = 2) -> List[str]:
    """
    Retrieve top-k semantically similar style exemplars.
    
    Args:
        style_bank: Name of the style bank
        lane: Target lane
        query: Query text for semantic matching
        k: Number of exemplars to retrieve (default: 2)
    
    Returns:
        List of exemplar texts
    """
    if "style_banks" not in st.session_state:
        return []
    
    if style_bank not in st.session_state.style_banks:
        return []
    
    bank = st.session_state.style_banks[style_bank]
    exemplars = bank.get(lane, [])
    
    if not exemplars:
        return []
    
    # Compute query vector
    query_vec = _simple_vec(query)
    
    # Score all exemplars
    scored = []
    for ex in exemplars:
        sim = _cosine_sim(query_vec, ex["vector"])
        scored.append({
            "text": ex["text"],
            "score": sim
        })
    
    # Sort and return top k
    scored.sort(key=lambda x: x["score"], reverse=True)
    return [s["text"] for s in scored[:k]]


def get_style_bank_stats(bank_name: str) -> Dict[str, int]:
    """
    Get exemplar counts per lane for a style bank.
    
    Returns:
        Dict mapping lane name to exemplar count
    """
    if "style_banks" not in st.session_state:
        return {lane: 0 for lane in ["Dialogue", "Narration", "Interiority", "Action"]}
    
    if bank_name not in st.session_state.style_banks:
        return {lane: 0 for lane in ["Dialogue", "Narration", "Interiority", "Action"]}
    
    bank = st.session_state.style_banks[bank_name]
    return {lane: len(bank.get(lane, [])) for lane in ["Dialogue", "Narration", "Interiority", "Action"]}


def list_style_banks() -> List[str]:
    """
    Get list of all style bank names.
    """
    if "style_banks" not in st.session_state:
        return []
    
    return list(st.session_state.style_banks.keys())


def delete_style_bank(bank_name: str) -> bool:
    """
    Delete an entire style bank.
    
    Returns:
        True if deleted, False if bank doesn't exist
    """
    if "style_banks" not in st.session_state:
        return False
    
    if bank_name not in st.session_state.style_banks:
        return False
    
    del st.session_state.style_banks[bank_name]
    return True
