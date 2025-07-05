"""
TV Show Reflector

Maintains shared scene context and conversation memory for coordinated AI behavior.
Provides scene summaries and context to all characters for scene-aware interactions.
Enhanced with emotional tone analysis and mood propagation.
"""

import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio


class SceneSummary:
    """Represents a summary of the current scene/context."""
    
    def __init__(self, 
                 summary: str,
                 discussion_theme: str,
                 active_characters: List[str],
                 emotional_tone: str,
                 scene_tone_score: float,
                 recent_triggers: List[str],
                 timestamp: float):
        self.summary = summary
        self.discussion_theme = discussion_theme
        self.active_characters = active_characters
        self.emotional_tone = emotional_tone
        self.scene_tone_score = scene_tone_score  # [-1.0, 1.0] for mood propagation
        self.recent_triggers = recent_triggers
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "summary": self.summary,
            "discussion_theme": self.discussion_theme,
            "active_characters": self.active_characters,
            "emotional_tone": self.emotional_tone,
            "scene_tone_score": self.scene_tone_score,
            "recent_triggers": self.recent_triggers,
            "timestamp": self.timestamp,
            "formatted_time": datetime.fromtimestamp(self.timestamp).isoformat()
        }


class Reflector:
    """
    Shared scene context manager for TV show characters.
    
    Maintains conversation log and provides periodic summaries
    to enable coordinated, scene-aware behavior.
    Enhanced with emotional tone analysis and mood propagation.
    """
    
    def __init__(self, 
                 summary_interval: int = 10,  # Summarize every N messages
                 max_log_size: int = 100):    # Max messages to keep
        self.conversation_log: List[Dict[str, Any]] = []
        self.scene_summaries: List[SceneSummary] = []
        self.summary_interval = summary_interval
        self.max_log_size = max_log_size
        self.last_summary_time = time.time()
        self.active_characters = set()
        self.recent_triggers = []
    
    def add_message(self, 
                   speaker: str, 
                   content: str, 
                   msg_type: str = "chat",
                   triggers: List[str] = None) -> None:
        """Add a message to the conversation log."""
        entry = {
            "timestamp": time.time(),
            "speaker": speaker,
            "content": content,
            "type": msg_type
        }
        
        self.conversation_log.append(entry)
        
        # Track active characters
        if speaker != "user":
            self.active_characters.add(speaker)
        
        # Track recent triggers
        if triggers:
            self.recent_triggers.extend(triggers)
            # Keep only last 5 triggers
            self.recent_triggers = self.recent_triggers[-5:]
        
        # Maintain log size
        if len(self.conversation_log) > self.max_log_size:
            self.conversation_log = self.conversation_log[-self.max_log_size:]
        
        # Check if we should generate a new summary
        if len(self.conversation_log) % self.summary_interval == 0:
            self._generate_summary()
    
    def _generate_summary(self) -> None:
        """Generate a new scene summary based on recent conversation."""
        if not self.conversation_log:
            return
        
        # Get recent messages for summarization
        recent_messages = self.conversation_log[-self.summary_interval:]
        
        # Simple heuristic-based summarization for now
        # (Can be replaced with LLM-based summarization later)
        summary = self._heuristic_summarize(recent_messages)
        
        # Create scene summary
        scene_summary = SceneSummary(
            summary=summary["summary"],
            discussion_theme=summary["theme"],
            active_characters=list(self.active_characters),
            emotional_tone=summary["tone"],
            scene_tone_score=summary["tone_score"],
            recent_triggers=self.recent_triggers.copy(),
            timestamp=time.time()
        )
        
        self.scene_summaries.append(scene_summary)
        
        # Keep only last 10 summaries
        if len(self.scene_summaries) > 10:
            self.scene_summaries = self.scene_summaries[-10:]
        
        print(f"🎭 Scene summary generated: {summary['summary'][:100]}... (tone: {summary['tone']}, score: {summary['tone_score']:.2f})")
    
    def _heuristic_summarize(self, messages: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate a heuristic-based summary of recent messages."""
        if not messages:
            return {
                "summary": "No recent activity",
                "theme": "quiet",
                "tone": "neutral",
                "tone_score": 0.0
            }
        
        # Extract content and speakers
        contents = [msg["content"] for msg in messages]
        speakers = [msg["speaker"] for msg in messages]
        
        # Simple theme detection
        themes = []
        if any("human" in content.lower() for content in contents):
            themes.append("humanity")
        if any("beauty" in content.lower() or "art" in content.lower() for content in contents):
            themes.append("aesthetics")
        if any("create" in content.lower() or "invent" in content.lower() for content in contents):
            themes.append("creativity")
        if any("existential" in content.lower() or "crisis" in content.lower() for content in contents):
            themes.append("philosophy")
        
        theme = themes[0] if themes else "general discussion"
        
        # Enhanced tone detection with score calculation
        tone_indicators = {
            "excited": ["!", "amazing", "incredible", "wow", "excited", "thrilled"],
            "melancholic": ["sad", "lonely", "existential", "crisis", "melancholy", "depressed"],
            "curious": ["?", "wonder", "curious", "think", "explore", "discover"],
            "creative": ["create", "invent", "imagine", "new", "innovative", "creative"],
            "frustrated": ["frustrated", "angry", "annoyed", "irritated", "tense"],
            "calm": ["calm", "peaceful", "serene", "relaxed", "content"],
            "positive": ["happy", "joy", "pleased", "satisfied", "optimistic"],
            "negative": ["unhappy", "disappointed", "pessimistic", "worried", "anxious"]
        }
        
        # Calculate tone score based on content analysis
        tone_score = 0.0
        tone_counts = {}
        
        for tone_name, indicators in tone_indicators.items():
            count = sum(1 for indicator in indicators 
                       for content in contents 
                       if indicator in content.lower())
            tone_counts[tone_name] = count
        
        # Calculate overall tone score
        positive_indicators = tone_counts.get("excited", 0) + tone_counts.get("creative", 0) + tone_counts.get("positive", 0) + tone_counts.get("curious", 0)
        negative_indicators = tone_counts.get("melancholic", 0) + tone_counts.get("frustrated", 0) + tone_counts.get("negative", 0)
        
        total_indicators = positive_indicators + negative_indicators
        if total_indicators > 0:
            tone_score = (positive_indicators - negative_indicators) / total_indicators
        else:
            tone_score = 0.0  # Neutral if no clear indicators
        
        # Clamp tone score to [-1.0, 1.0]
        tone_score = max(-1.0, min(1.0, tone_score))
        
        # Determine primary tone
        tone = "neutral"
        max_count = 0
        for tone_name, count in tone_counts.items():
            if count > max_count:
                max_count = count
                tone = tone_name
        
        # Generate summary
        unique_speakers = list(set(speakers))
        summary = f"Recent conversation involves {', '.join(unique_speakers)} discussing {theme} in a {tone} tone."
        
        return {
            "summary": summary,
            "theme": theme,
            "tone": tone,
            "tone_score": tone_score
        }
    
    def get_current_scene_summary(self) -> Optional[SceneSummary]:
        """Get the most recent scene summary."""
        if not self.scene_summaries:
            return None
        return self.scene_summaries[-1]
    
    def get_scene_context_for_character(self, character_id: str) -> str:
        """Get scene context formatted for a specific character."""
        current_summary = self.get_current_scene_summary()
        
        if not current_summary:
            return "The scene is quiet with no recent activity."
        
        context = f"Current scene: {current_summary.summary}\n"
        context += f"Discussion theme: {current_summary.discussion_theme}\n"
        context += f"Active participants: {', '.join(current_summary.active_characters)}\n"
        context += f"Emotional tone: {current_summary.emotional_tone}"
        
        if current_summary.recent_triggers:
            context += f"\nRecent events: {', '.join(current_summary.recent_triggers)}"
        
        return context
    
    def get_scene_tone_for_mood_propagation(self) -> tuple[str, float]:
        """Get scene tone for mood propagation to characters."""
        current_summary = self.get_current_scene_summary()
        if not current_summary:
            return "neutral", 0.0
        
        return current_summary.emotional_tone, current_summary.scene_tone_score
    
    def get_full_log(self) -> List[Dict[str, Any]]:
        """Get the full conversation log."""
        return self.conversation_log.copy()
    
    def get_summaries(self) -> List[Dict[str, Any]]:
        """Get all scene summaries."""
        return [summary.to_dict() for summary in self.scene_summaries]
    
    def get_scene_stats(self) -> Dict[str, Any]:
        """Get current scene statistics."""
        current_summary = self.get_current_scene_summary()
        return {
            "total_messages": len(self.conversation_log),
            "active_characters": list(self.active_characters),
            "recent_triggers": self.recent_triggers.copy(),
            "summaries_count": len(self.scene_summaries),
            "last_summary_time": self.last_summary_time,
            "current_tone": current_summary.emotional_tone if current_summary else "neutral",
            "current_tone_score": current_summary.scene_tone_score if current_summary else 0.0
        } 