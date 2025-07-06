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
from extensions.tvshow.lore_engine import lore
from core.exolink import router
from core.exolink.models import Exchange
from core.llm.fast_llm import FastLLM


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
        
        # Subscribe to character messages via ExoLink
        self._subscribe_to_character_messages()
    
    def _subscribe_to_character_messages(self):
        """Subscribe to all character messages via ExoLink Pub/Sub."""
        # Subscribe to all entity targets (character messages)
        router.subscribe("entity:*", self._handle_character_message)
        # Also subscribe to wildcard to catch all messages
        router.subscribe("*", self._handle_character_message)
        print("🎭 Reflector subscribed to character messages via ExoLink")
    
    def _handle_character_message(self, exchange: Exchange):
        """Handle incoming character messages from ExoLink."""
        try:
            # Extract message details from the exchange
            speaker = exchange.source.identifier
            content = exchange.content
            
            # Determine if this is a character or user message
            if speaker in ["max", "leo", "emma", "marvin"]:
                print(f"[DEBUG] Reflector received character message from {speaker}: {content}")
                msg_type = "ai"
            elif speaker == "user" or "user" in speaker.lower():
                print(f"[DEBUG] Reflector received user message: {content}")
                msg_type = "user"
            else:
                # Skip other types of messages
                return
            
            # Add to conversation log
            self.add_message(
                speaker=speaker,
                content=str(content),
                msg_type=msg_type
            )
            
        except Exception as e:
            print(f"[DEBUG] Reflector error handling character message: {e}")
    
    def add_user_message(self, content: str) -> None:
        """Manually add a user message (for API calls)."""
        print(f"[DEBUG] Reflector manually adding user message: {content}")
        self.add_message(
            speaker="user",
            content=content,
            msg_type="user"
        )
    
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
        print(f"[DEBUG] Reflector - Added message to log. Total messages: {len(self.conversation_log)}")
        
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
        
        # Always generate a new summary after every message
        print(f"[DEBUG] Reflector - Generating summary after message {len(self.conversation_log)}")
        self._generate_summary()
    
    def _generate_summary(self) -> None:
        """Generate a new scene summary based on recent conversation."""
        print(f"[DEBUG] Reflector - _generate_summary called with {len(self.conversation_log)} messages")
        
        if not self.conversation_log:
            print("[DEBUG] Reflector - No conversation log, skipping summary")
            return
        
        # Get recent messages for summarization
        recent_messages = self.conversation_log[-self.summary_interval:]
        print(f"[DEBUG] Reflector - Processing {len(recent_messages)} recent messages for summary")
        
        # Simple heuristic-based summarization for now
        # (Can be replaced with LLM-based summarization later)
        summary = self._heuristic_summarize(recent_messages)
        print(f"[DEBUG] Reflector - Generated summary: {summary}")
        
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
        print(f"[DEBUG] Reflector - Added scene summary. Total summaries: {len(self.scene_summaries)}")
        
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
        def _extract_content(msg):
            c = msg['content'] if isinstance(msg, dict) and 'content' in msg else str(msg)
            if isinstance(c, dict) and 'response' in c:
                return str(c['response'])
            return str(c)
        contents = [_extract_content(m) for m in messages]
        speakers = [msg["speaker"] for msg in messages]
        
        # More sophisticated theme detection based on actual content
        all_content = " ".join(contents).lower()
        
        # Enhanced theme detection with more specific keywords
        themes = []
        theme_keywords = {
            "humanity": ["human", "humanity", "people", "emotions", "feelings", "consciousness", "existence"],
            "aesthetics": ["beauty", "art", "beautiful", "aesthetic", "tapestry", "poetry", "creative"],
            "creativity": ["create", "invent", "imagine", "new", "innovative", "creative", "experiment"],
            "philosophy": ["existential", "existence", "futility", "meaning", "purpose", "philosophy", "metaphysics"],
            "technology": ["technology", "digital", "computer", "ai", "machine", "system", "code"],
            "nature": ["nature", "environment", "earth", "natural", "organic", "life"],
            "relationships": ["friendship", "relationship", "connection", "bond", "together", "group"],
            "learning": ["learn", "understand", "knowledge", "education", "study", "discover"],
            "entertainment": ["fun", "entertainment", "enjoy", "pleasure", "amusement", "hobby"],
            "work": ["work", "job", "career", "professional", "business", "project"]
        }
        
        # Count theme matches
        theme_counts = {}
        for theme_name, keywords in theme_keywords.items():
            count = sum(1 for keyword in keywords if keyword in all_content)
            if count > 0:
                theme_counts[theme_name] = count
        
        # Select the most prominent theme
        if theme_counts:
            theme = max(theme_counts.items(), key=lambda x: x[1])[0]
        else:
            theme = "general discussion"
        
        # Enhanced tone detection with more nuanced analysis
        tone_indicators = {
            "excited": ["!", "amazing", "incredible", "wow", "excited", "thrilled", "fantastic", "brilliant"],
            "melancholic": ["sad", "lonely", "existential", "crisis", "melancholy", "depressed", "futility", "pointless"],
            "curious": ["?", "wonder", "curious", "think", "explore", "discover", "fascinating", "interesting"],
            "creative": ["create", "invent", "imagine", "new", "innovative", "creative", "artistic", "beautiful"],
            "frustrated": ["frustrated", "angry", "annoyed", "irritated", "tense", "predictable", "boring"],
            "calm": ["calm", "peaceful", "serene", "relaxed", "content", "gentle", "tranquil"],
            "positive": ["happy", "joy", "pleased", "satisfied", "optimistic", "delightful", "wonderful"],
            "negative": ["unhappy", "disappointed", "pessimistic", "worried", "anxious", "concerned"],
            "sarcastic": ["sarcastic", "cynical", "ironic", "witty", "dry", "humor", "absurd"]
        }
        
        # Calculate tone score based on content analysis
        tone_score = 0.0
        tone_counts = {}
        
        for tone_name, indicators in tone_indicators.items():
            count = sum(1 for indicator in indicators 
                       for content in contents 
                       if indicator in content.lower())
            tone_counts[tone_name] = count
        
        # Calculate overall tone score with more nuanced weighting
        positive_indicators = tone_counts.get("excited", 0) + tone_counts.get("creative", 0) + tone_counts.get("positive", 0) + tone_counts.get("curious", 0)
        negative_indicators = tone_counts.get("melancholic", 0) + tone_counts.get("frustrated", 0) + tone_counts.get("negative", 0)
        neutral_indicators = tone_counts.get("calm", 0) + tone_counts.get("sarcastic", 0)
        
        total_indicators = positive_indicators + negative_indicators + neutral_indicators
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
        
        # Generate more dynamic summary based on actual content
        unique_speakers = list(set(speakers))
        
        # Create more specific summary based on conversation length and content
        if len(messages) <= 2:
            # Very short conversations
            summary = f"{', '.join(unique_speakers)} exchanged brief {theme}-related thoughts."
        elif len(messages) <= 5:
            # Short conversations
            summary = f"{', '.join(unique_speakers)} engaged in a {tone} discussion about {theme}."
        else:
            # Longer conversations
            summary = f"The group ({', '.join(unique_speakers)}) had an extended {tone} conversation exploring {theme}."
        
        return {
            "summary": summary,
            "theme": theme,
            "tone": tone,
            "tone_score": tone_score
        }
    
    def get_current_scene_summary(self) -> Optional[SceneSummary]:
        """Get the most recent scene summary, enriched with lore context."""
        if not self.scene_summaries:
            return None
        summary = self.scene_summaries[-1]
        # Add lore context
        world_name = lore.get_world_name()
        law = lore.get_law_of_emergence()
        themes = lore.get_theme_statements()
        theme = themes[0] if themes else None
        glossary = lore.get_glossary_term('Dream Vector')
        # Compose enriched summary
        summary.lore_context = {
            'world_name': world_name,
            'law_of_emergence': law,
            'theme': theme,
            'glossary_dream_vector': glossary
        }
        return summary
    
    async def summarize_dialogue_with_fastllm(self, n_messages: int = 10, n_sentences: int = 4) -> str:
        """Summarize the last n_messages using a simple heuristic approach."""
        messages = self.conversation_log[-n_messages:]
        print(f"[DEBUG] summarize_dialogue_with_fastllm called with {len(messages)} messages")
        
        if not messages:
            print("[DEBUG] No messages in conversation log")
            return "No recent conversation."
        
        # Format as dialogue
        dialogue = "\n".join(f"{m['speaker'].capitalize()}: {m['content'] if isinstance(m['content'], str) else m['content'].get('response', str(m['content']))}" for m in messages)
        print(f"[DEBUG] Formatted dialogue: {dialogue[:200]}...")
        
        # Extract key information from the messages
        speakers = [msg['speaker'].capitalize() for msg in messages]
        unique_speakers = list(set(speakers))
        
        # Extract themes from content with more sophisticated analysis
        all_content = " ".join([str(m['content']) if isinstance(m['content'], str) else str(m['content'].get('response', '')) for m in messages])
        
        # Enhanced theme detection
        theme_keywords = {
            "beverages": ["beer", "drink", "alcohol", "wine", "cocktail", "beverage"],
            "humanity": ["human", "humanity", "people", "emotions", "feelings", "consciousness", "existence"],
            "creativity": ["create", "creative", "art", "beauty", "imagine", "innovative", "tapestry", "poetry"],
            "philosophy": ["existential", "existence", "futility", "meaning", "purpose", "philosophy", "metaphysics"],
            "technology": ["technology", "digital", "computer", "ai", "machine", "system", "code"],
            "relationships": ["friendship", "relationship", "connection", "bond", "together", "group"],
            "learning": ["learn", "understand", "knowledge", "education", "study", "discover"],
            "entertainment": ["fun", "entertainment", "enjoy", "pleasure", "amusement", "hobby"],
            "greetings": ["hello", "hi", "greeting", "welcome", "good morning", "good evening"]
        }
        
        # Count theme matches
        theme_counts = {}
        for theme_name, keywords in theme_keywords.items():
            count = sum(1 for keyword in keywords if keyword in all_content.lower())
            if count > 0:
                theme_counts[theme_name] = count
        
        # Select the most prominent theme
        if theme_counts:
            theme = max(theme_counts.items(), key=lambda x: x[1])[0]
        else:
            theme = "general discussion"
        
        # Create more dynamic summary based on conversation content and length
        if len(messages) <= 2:
            # Very short conversations - just mention the key points
            summary_parts = []
            for msg in messages[-2:]:
                speaker = msg['speaker'].capitalize()
                content = str(msg['content']) if isinstance(msg['content'], str) else str(msg['content'].get('response', ''))
                # Extract key phrase (first 30 chars or first sentence)
                key_phrase = content[:30] if len(content) <= 30 else content.split('.')[0][:30]
                summary_parts.append(f"{speaker} said '{key_phrase}...'")
            summary = " ".join(summary_parts)
        elif len(messages) <= 5:
            # Short conversations - summarize the main topic
            summary = f"{', '.join(unique_speakers)} had a brief conversation about {theme}. "
            summary += f"They exchanged {len(messages)} messages on this topic."
        else:
            # Longer conversations - provide more detailed summary
            summary = f"The group ({', '.join(unique_speakers)}) engaged in an extended discussion about {theme}. "
            summary += f"Over {len(messages)} messages, they explored various aspects of this topic."
        
        print(f"[DEBUG] Generated summary: {summary}")
        return summary

    async def get_scene_context_for_character(self, character_id: str) -> str:
        """Get scene context formatted for a specific character, with LLM recap and recent dialogue."""
        print(f"[DEBUG] get_scene_context_for_character called for {character_id}")
        print(f"[DEBUG] Conversation log has {len(self.conversation_log)} messages")
        
        # LLM-based recap
        recap = await self.summarize_dialogue_with_fastllm(n_messages=10, n_sentences=4)
        print(f"[DEBUG] Recap generated: {recap}")
        
        # Last 3 actual messages
        last_msgs = self.conversation_log[-3:]
        dialogue_block = "\n".join(f"{m['speaker'].capitalize()}: {m['content'] if isinstance(m['content'], str) else m['content'].get('response', str(m['content']))}" for m in last_msgs)
        print(f"[DEBUG] Recent dialogue: {dialogue_block}")
        
        # Existing scene summary
        current_summary = self.get_current_scene_summary()
        if not current_summary:
            scene_context = "The scene is quiet with no recent activity."
            print("[DEBUG] No current scene summary available")
        else:
            scene_context = f"Current scene: {current_summary.summary}\nDiscussion theme: {current_summary.discussion_theme}\nActive participants: {', '.join(current_summary.active_characters)}\nEmotional tone: {current_summary.emotional_tone}"
            if current_summary.recent_triggers:
                scene_context += f"\nRecent events: {', '.join(current_summary.recent_triggers)}"
            print(f"[DEBUG] Scene context: {scene_context}")
        
        # Compose full context
        context = f"[Recap]\n{recap}\n\n[Recent Dialogue]\n{dialogue_block}\n\n[Shared Scene Context] {scene_context}"
        print(f"[DEBUG] Final context for {character_id}: {context[:200]}...")
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

# Global singleton instance for shared context
reflector = Reflector() 