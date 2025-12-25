# ============================================================
# OLIVETTI ANALYTICS & USAGE TRACKING
# Privacy-focused analytics for understanding usage patterns
# ============================================================

import json
import time
from typing import Dict, Any, List
from datetime import datetime, timedelta
import streamlit as st

class UsageAnalytics:
    """Track usage patterns and generate insights"""
    
    def __init__(self):
        self.session_start = time.time()
        self.events: List[Dict[str, Any]] = []
    
    def track_event(self, event_type: str, metadata: Dict[str, Any] = None):
        """Track a usage event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "metadata": metadata or {},
        }
        self.events.append(event)
        
        # Keep only last 1000 events to prevent memory bloat
        if len(self.events) > 1000:
            self.events = self.events[-1000:]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        session_duration = time.time() - self.session_start
        
        event_counts = {}
        for event in self.events:
            event_type = event["type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "session_duration_minutes": round(session_duration / 60, 1),
            "total_events": len(self.events),
            "event_breakdown": event_counts,
        }
    
    def get_writing_stats(self) -> Dict[str, Any]:
        """Get writing-specific statistics"""
        write_events = [e for e in self.events if e["type"] in ["write", "rewrite", "expand", "trim"]]
        
        if not write_events:
            return {"total_ai_actions": 0, "avg_words_per_action": 0}
        
        total_words = sum(e.get("metadata", {}).get("word_count", 0) for e in write_events)
        
        return {
            "total_ai_actions": len(write_events),
            "avg_words_per_action": round(total_words / len(write_events)) if write_events else 0,
            "actions_by_type": {
                action: len([e for e in write_events if e["type"] == action])
                for action in ["write", "rewrite", "expand", "trim"]
            }
        }
    
    def export_analytics(self) -> str:
        """Export analytics as JSON"""
        return json.dumps({
            "exported_at": datetime.now().isoformat(),
            "session_stats": self.get_session_stats(),
            "writing_stats": self.get_writing_stats(),
            "events": self.events[-100:],  # Last 100 events only
        }, indent=2)


class ProjectAnalytics:
    """Track project-level analytics"""
    
    @staticmethod
    def analyze_project(project: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single project"""
        draft = project.get("draft", "")
        story_bible = project.get("story_bible", {}) or {}
        
        word_count = len(draft.split()) if draft else 0
        char_count = len(draft)
        
        # Story Bible completeness
        sb_sections = ["synopsis", "genre_style_notes", "world", "characters", "outline"]
        filled_sections = sum(1 for s in sb_sections if (story_bible.get(s) or "").strip())
        sb_completeness = (filled_sections / len(sb_sections)) * 100
        
        # Voice training
        voices = project.get("voices", {})
        total_voice_samples = 0
        for voice in voices.values():
            for lane in voice.get("lanes", {}).values():
                total_voice_samples += len(lane)
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "story_bible_completeness": round(sb_completeness, 1),
            "voice_training_samples": total_voice_samples,
            "created": project.get("created_ts", ""),
            "last_updated": project.get("updated_ts", ""),
        }
    
    @staticmethod
    def analyze_all_projects(projects: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze all projects"""
        if not projects:
            return {
                "total_projects": 0,
                "total_words": 0,
                "avg_words_per_project": 0,
            }
        
        project_analyses = [ProjectAnalytics.analyze_project(p) for p in projects.values()]
        
        total_words = sum(p["word_count"] for p in project_analyses)
        total_samples = sum(p["voice_training_samples"] for p in project_analyses)
        avg_completeness = sum(p["story_bible_completeness"] for p in project_analyses) / len(project_analyses)
        
        # Projects by bay
        projects_by_bay = {}
        for proj in projects.values():
            bay = proj.get("bay", "NEW")
            projects_by_bay[bay] = projects_by_bay.get(bay, 0) + 1
        
        return {
            "total_projects": len(projects),
            "total_words": total_words,
            "avg_words_per_project": round(total_words / len(projects)) if projects else 0,
            "total_voice_samples": total_samples,
            "avg_story_bible_completeness": round(avg_completeness, 1),
            "projects_by_bay": projects_by_bay,
        }


def track_action(action_type: str, metadata: Dict[str, Any] = None):
    """Helper to track an action"""
    if hasattr(st.session_state, 'analytics'):
        st.session_state.analytics.track_event(action_type, metadata)


def init_analytics():
    """Initialize analytics tracking"""
    if "analytics" not in st.session_state:
        st.session_state.analytics = UsageAnalytics()


# Auto-initialize on import
if "analytics" not in st.session_state:
    init_analytics()
