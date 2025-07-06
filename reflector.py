"""
TV Show Reflector

Maintains shared scene context and conversation memory for coordinated AI behavior.
Provides scene summaries and context to all characters for scene-aware interactions.
Enhanced with emotional tone analysis and mood propagation.
"""

import time
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
from extensions.tvshow.lore_engine import lore
from core.exolink import router
from core.exolink.models import Exchange, Source, Target, SourceType, TargetType
from core.llm.fast_llm import FastLLM
from core.entity import BaseEntity


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


class Reflector(BaseEntity):
    """
    Shared scene context manager for TV show characters.
    
    Maintains conversation log and provides periodic summaries
    to enable coordinated, scene-aware behavior.
    Enhanced with emotional tone analysis and mood propagation.
    """
    
    # Entity configuration
    IDENTITY_PATH = Path(__file__).parent / "reflector_identity"
    
    def __init__(self, 
                 summary_interval: int = 10,  # Summarize every N messages
                 max_log_size: int = 100):    # Max messages to keep
        # Initialize as BaseEntity first
        super().__init__()
        
        self.conversation_log: List[Dict[str, Any]] = []
        self.scene_summaries: List[SceneSummary] = []
        self.summary_interval = summary_interval
        self.max_log_size = max_log_size
        self.last_summary_time = time.time()
        self.active_characters = set()
        self.recent_triggers = []
        
        # Subscribe to character messages via ExoLink
        self._subscribe_to_character_messages()
    
    def _load_identity(self) -> Dict[str, Any]:
        """Load neutral identity configuration for analysis tasks."""
        return {
            "name": "Scene Reflector",
            "personality": {"summary": "A neutral scene analysis assistant"},
            "module_paths": {"performance_config": {}},
            "system_prompts": {
                "en": "You are a neutral scene analysis assistant. Your role is to analyze conversations and provide objective summaries.",
                "ru": "Вы нейтральный помощник для анализа сцен. Ваша роль - анализировать разговоры и предоставлять объективные резюме."
            },
            "llm_instructions": "You are a neutral analysis assistant focused on providing objective conversation analysis.",
            "module_paths": {
                "local_llm_binary": "models/llama.cpp/build/bin/llama",
                "local_model_gguf": "models/phi-4-Q4_K.gguf",
                "memory_dir": "storage/chroma",
                "performance_config": {
                "gpu_layers": 35,
                "context_size": 8192,
                "batch_size": 256,
                "threads": 8
                }
            }
        }
    
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
            
            # Check if this is a proxy message (AI response sent through ExoLink)
            if exchange.metadata.get("_proxy_target", False):
                # This is an AI response sent through ExoLink - use the original source
                speaker = exchange.source.identifier  # This is the actual character (e.g., "max")
                print(f"[DEBUG] Reflector received proxy AI message from {speaker}: {content}")
                msg_type = "ai"
            elif speaker in ["max", "leo", "emma", "marvin"]:
                print(f"[DEBUG] Reflector received character message from {speaker}: {content}")
                msg_type = "ai"
            elif speaker == "user" or "user" in speaker.lower():
                print(f"[DEBUG] Reflector received user message: {content}")
                msg_type = "user"
            else:
                # Skip other types of messages
                return
            
            # Extract actual response text if content is a response object
            actual_content = content
            if isinstance(content, dict) and "response" in content:
                actual_content = content["response"]
            elif isinstance(content, str):
                actual_content = content
            else:
                actual_content = str(content)
            
            # Add to conversation log (always await async method)
            asyncio.create_task(self.add_message(
                speaker=speaker,
                content=actual_content,
                msg_type=msg_type
            ))
            
            # --- NEW: Character-to-character orchestration via ExoLink ---
            if (speaker in ["max", "leo", "emma", "marvin"] and 
                not exchange.metadata.get("_orchestrated", False)):
                addressed_character = self._detect_addressed_character(speaker, actual_content)
                if addressed_character:
                    print(f"[DEBUG] Reflector detected character-to-character: {speaker} > {addressed_character}")
                    asyncio.create_task(self._trigger_character_handoff(
                        from_character=speaker,
                        to_character=addressed_character,
                        original_content=actual_content
                    ))
        except Exception as e:
            print(f"[DEBUG] Reflector error handling character message: {e}")
    
    def _detect_addressed_character(self, speaker: str, content: str) -> Optional[str]:
        """Detect if a message addresses another character."""
        # Get all character names
        from .entities import get_all_characters
        all_character_names = list(get_all_characters().keys())
        
        # If speaker is a character, exclude them from the list
        if speaker in all_character_names:
            character_names = [name for name in all_character_names if name != speaker]
        else:
            # If speaker is "user" or not a character, include all character names
            character_names = all_character_names
        
        if not character_names:
            return None
        
        # Regex: look for character names followed by comma, colon, space, or other punctuation
        # More flexible pattern that catches names after any word, not just word boundaries
        pattern = r'(%s)[,:\s?!.]' % "|".join([re.escape(name.capitalize()) for name in character_names])
        matches = list(re.finditer(pattern, content))
        
        if matches:
            addressed_name = matches[0].group(1).lower()
            print(f"[DEBUG] Detected addressed character: {addressed_name} in content: {content[:100]}...")
            return addressed_name
        
        return None
    
    async def _trigger_character_handoff(self, from_character: str, to_character: str, original_content: str):
        """Trigger a character-to-character handoff via ExoLink."""
        try:
            print(f"[DEBUG] Triggering ExoLink handoff: {from_character} > {to_character}")
            
            # Create source and target for ExoLink
            source = Source(type=SourceType.ENTITY, identifier=from_character)
            target = Target(type=TargetType.ENTITY, identifier=to_character)
            
            # Add metadata to prevent infinite loops
            metadata = {
                "_orchestrated": True,
                "_handoff_from": from_character,
                "_original_content": original_content,
                "_handoff_timestamp": time.time()
            }
            
            # Send via ExoLink - this will trigger the character's registered handler
            # router.send() returns a coroutine that must be awaited
            result = await router.send(
                content=original_content,
                source=source,
                target=target,
                metadata=metadata
            )
            
            print(f"[DEBUG] ExoLink handoff completed: {from_character} > {to_character}")
            print(f"[DEBUG] Handoff result: {result}")
            
        except Exception as e:
            print(f"[DEBUG] ExoLink handoff failed: {e}")
            import traceback
            traceback.print_exc()
    
    def add_user_message(self, content: str) -> None:
        """Manually add a user message (for API calls)."""
        print(f"[DEBUG] Reflector manually adding user message: {content}")
        asyncio.create_task(self.add_message(
            speaker="user",
            content=content,
            msg_type="user"
        ))
        addressed_character = self._detect_addressed_character("user", content)
        if addressed_character:
            print(f"[DEBUG] Reflector detected user addressing character: user > {addressed_character}")
            asyncio.create_task(self._trigger_character_handoff(
                from_character="user",
                to_character=addressed_character,
                original_content=content
            ))
    
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
            # Use the entity's LocalLLM instance (inherits neutral identity)
            response = await self.llm_router.local_llm.generate(
                prompt=f"""Analyze this conversation and provide a structured summary in JSON format:

{dialogue}

Provide a JSON response with:
- summary: 1-2 sentence summary of what was discussed
- theme: the main topic/theme (be specific, e.g., "beer brewing", "human emotions", "technology")
- tone: the overall emotional tone (excited, calm, curious, etc.)
- tone_score: a number between 0-1 indicating intensity

JSON:""",
                max_tokens=200
            )
            
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
            # Use the entity's LocalLLM instance (inherits neutral identity)
            response = await self.llm_router.local_llm.generate(
                prompt=f"""Analyze this conversation and provide a brief summary (2-3 sentences) of what was discussed:

{dialogue}

Summary:""",
                max_tokens=100
            )
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
        
        # Label the last message with the correct sender
        last_message = last_msgs[-1] if last_msgs else None
        if last_message:
            sender = last_message['speaker'].capitalize()
            labeled_last_message = f"[{sender}'s message] {last_message['content'] if isinstance(last_message['content'], str) else last_message['content'].get('response', str(last_message['content']))}"
        else:
            labeled_last_message = ""
        
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
        context = f"[Recap]\n{recap}\n\n[Recent Dialogue]\n{dialogue_block}\n\n{labeled_last_message}\n\n[Shared Scene Context] {scene_context}"
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