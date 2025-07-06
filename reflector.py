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
    
    async def add_message(self, 
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
        summary = await self._generate_summary(self.conversation_log[-self.summary_interval:])
        
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
    
    async def _generate_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of recent messages using LocalLLM."""
        if not messages:
            return {
                "summary": "No recent activity",
                "theme": "quiet",
                "tone": "neutral",
                "tone_score": 0.0
            }
        
        # Format as dialogue for LLM analysis
        dialogue = "\n".join(f"{m['speaker'].capitalize()}: {m['content'] if isinstance(m['content'], str) else m['content'].get('response', str(m['content']))}" for m in messages)
        
        try:
            # Use LocalLLM for accurate analysis
            from core.llm.local_llm import LocalLLM
            llm = LocalLLM()
            
            prompt = f"""Analyze this conversation and provide a structured summary in JSON format:

{dialogue}

Provide a JSON response with:
- summary: 1-2 sentence summary of what was discussed
- theme: the main topic/theme (be specific, e.g., "beer brewing", "human emotions", "technology")
- tone: the overall emotional tone (excited, calm, curious, etc.)
- tone_score: a number between 0-1 indicating intensity

JSON:"""
            
            response = await llm.generate(prompt, max_tokens=200)
            
            # Try to parse JSON response
            import json
            import re
            try:
                # Clean up the response - remove any extra text before/after JSON
                cleaned_response = response.strip()
                # Find JSON object in the response
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    cleaned_response = json_match.group(0)
                
                result = json.loads(cleaned_response)
                print(f"[DEBUG] LocalLLM generated scene summary: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSON parsing failed: {e}")
                # Fallback if JSON parsing fails
                return {
                    "summary": response.strip()[:100],
                    "theme": "general discussion",
                    "tone": "neutral",
                    "tone_score": 0.5
                }
                
        except Exception as e:
            print(f"[DEBUG] LocalLLM scene summary failed: {e}")
            # Fallback to simple summary
            speakers = [msg['speaker'].capitalize() for msg in messages]
            unique_speakers = list(set(speakers))
            return {
                "summary": f"{', '.join(unique_speakers)} had a conversation.",
                "theme": "general discussion",
                "tone": "neutral",
                "tone_score": 0.5
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
        """Summarize the last n_messages using LocalLLM for accurate theme detection."""
        messages = self.conversation_log[-n_messages:]
        print(f"[DEBUG] summarize_dialogue_with_fastllm called with {len(messages)} messages")
        
        if not messages:
            print("[DEBUG] No messages in conversation log")
            return "No recent conversation."
        
        # Format as dialogue
        dialogue = "\n".join(f"{m['speaker'].capitalize()}: {m['content'] if isinstance(m['content'], str) else m['content'].get('response', str(m['content']))}" for m in messages)
        print(f"[DEBUG] Formatted dialogue: {dialogue[:200]}...")
        
        try:
            # Use LocalLLM for accurate summarization
            from core.llm.local_llm import LocalLLM
            llm = LocalLLM()
            
            prompt = f"""Analyze this conversation and provide a brief summary (2-3 sentences) of what was discussed:

{dialogue}

Summary:"""
            
            response = await llm.generate(prompt, max_tokens=100)
            summary = response.strip()
            print(f"[DEBUG] LocalLLM generated summary: {summary}")
            return summary
            
        except Exception as e:
            print(f"[DEBUG] LocalLLM summarization failed: {e}")
            # Fallback to simple join
            fallback_messages = [f"{m['speaker'].capitalize()}: {m['content'] if isinstance(m['content'], str) else m['content'].get('response', str(m['content']))}" for m in messages[-3:]]
            return " ".join(fallback_messages)

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