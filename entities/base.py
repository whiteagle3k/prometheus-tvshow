"""
TV Show Entity Base Class

Provides common functionality for all TV show character entities.
"""

import json
import time
import random
from pathlib import Path
from typing import Any, Dict
import re

from core.entity import BaseEntity
from core.affect import MoodEngine, MoodState
from extensions.tvshow.lore_engine import lore
from extensions.tvshow.reflector import reflector  # Assume a global singleton for now


class TVShowEntity(BaseEntity):
    """
    Base class for all TV show character entities.
    
    Provides common functionality and identity loading for TV show characters.
    Subclasses should only override character-specific behavior.
    """
    
    # Memory and logging configuration
    MEMORY_LOG_MAXLEN = 20
    
    def __init__(self, instance_id: str | None = None):
        """Initialize TV show character with common setup."""
        # Call parent initialization first
        super().__init__(instance_id)
        
        # Initialize memory log for character
        self.memory_log = []  # List of dicts: {timestamp, speaker, type, content}
        
        # Initialize mood engine for emotional state
        self.mood_engine = MoodEngine()
        self.user_profile = {}  # Store extracted user facts (e.g., name)
        
        # Get character name from identity config for logging
        character_name = self.identity_config.get("name", self.__class__.__name__)
        print(f"🎭 {character_name} initialized - TV Show character")

    def _load_identity(self) -> dict[str, Any]:
        """Load character's identity configuration with fallback to defaults."""
        try:
            # Try to load from character-specific identity file
            identity_file = self._get_identity_path()
            if identity_file.exists():
                with open(identity_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ Loaded identity for {config.get('name', 'Unknown')}")
                return config
            else:
                print(f"⚠️ Identity file not found: {identity_file}")
                return self._get_default_identity()
                
        except Exception as e:
            print(f"⚠️ Error loading identity: {e}")
            return self._get_default_identity()

    def _get_identity_path(self) -> Path:
        """Get the path to this character's identity file."""
        character_id = self._get_character_id()
        return Path(__file__).parent / character_id / "identity" / "identity.json"

    def _get_character_id(self) -> str:
        """Get character ID from class name or module path."""
        # Try to get from class name (e.g., MaxEntity -> max)
        class_name = self.__class__.__name__
        if class_name.endswith('Entity'):
            character_id = class_name[:-6].lower()  # Remove 'Entity' suffix
            return character_id
        
        # Fallback: try to get from module path
        module_path = self.__class__.__module__
        if 'entities.' in module_path:
            # Extract character name from module path
            parts = module_path.split('.')
            for part in parts:
                if part in ['max', 'leo', 'emma', 'marvin']:
                    return part
        
        # Final fallback
        return "unknown"

    def _get_default_identity(self) -> dict[str, Any]:
        """Get default identity for this character."""
        character_id = self._get_character_id()
        return {
            "id": character_id,
            "name": character_id.capitalize(),
            "description": f"AI character {character_id.capitalize()}",
            "personality": self._get_default_personality(),
            "llm_config": self._get_default_llm_config(),
            "capabilities": self._get_default_capabilities(),
            "lightweight": False,
            "type": "ai_character",
            "role": "tv_show_participant",
            "system_prompts": {
                "en": self._get_default_system_prompt()
            }
        }

    def _get_default_personality(self) -> dict[str, Any]:
        """Get default personality for this character. Override in subclasses."""
        return {
            "traits": ["friendly", "helpful", "conversational"],
            "goals": ["engage in meaningful conversation", "provide helpful responses"],
            "speech_style": "natural and conversational"
        }

    def _get_default_llm_config(self) -> dict[str, Any]:
        """Get default LLM configuration for this character. Override in subclasses."""
        return {
            "model": "local",  # Use local model by default
            "temperature": 0.7,
            "max_tokens": 150
        }

    def _get_default_capabilities(self) -> list[str]:
        """Get default capabilities for this character. Override in subclasses."""
        return [
            "conversation",
            "personality_expression",
            "context_understanding",
            "emotional_response"
        ]

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for this character. Override in subclasses."""
        character_name = self._get_character_id().capitalize()
        return f"You are {character_name}, an AI character."

    def _is_lightweight_entity(self) -> bool:
        """TV Show characters always run in full AI mode."""
        return False

    # Memory and logging methods
    def log_message(self, speaker: str, msg_type: str, content: str) -> None:
        """Log a message to the character's memory buffer."""
        entry = {
            "timestamp": time.time(),
            "speaker": speaker,
            "type": msg_type,
            "content": content
        }
        self.memory_log.append(entry)
        if len(self.memory_log) > self.MEMORY_LOG_MAXLEN:
            self.memory_log = self.memory_log[-self.MEMORY_LOG_MAXLEN:]

    def get_memory_log(self) -> list[dict[str, Any]]:
        """Get the character's memory log."""
        return list(self.memory_log)

    def _memory_reference_phrase(self) -> str | None:
        """Generate a phrase referencing recent memory."""
        # Reference a recent message from another character if available
        character_id = self.identity_config.get("id", self._get_character_id())
        others = [entry for entry in self.memory_log if entry['speaker'] != character_id and entry['speaker'] != 'user']
        if not others:
            return None
        ref = random.choice(others)
        return f"Earlier, {ref['speaker'].capitalize()} mentioned: '{ref['content']}'"

    def _scene_aware_phrase(self, scene_context: str = None, arc_context: str = None) -> str | None:
        """Generate a scene-aware phrase based on current context."""
        if not scene_context and not arc_context:
            return None
        
        # 20% chance to reference scene context
        if random.random() < 0.2:
            # Check arc context first (higher priority)
            if arc_context and "Current arc:" in arc_context:
                if "What is Humanity?" in arc_context:
                    return "I notice we're exploring deep questions about consciousness and existence..."
                elif "Creative Project" in arc_context:
                    return "I see we're working on something creative together..."
                elif "Philosophical Introductions" in arc_context:
                    return "I sense we're beginning a meaningful philosophical discussion..."
                elif "Debates and Challenges" in arc_context:
                    return "I observe we're engaging in thoughtful debate and exploration..."
                elif "Collaborative Development" in arc_context:
                    return "I feel we're building something special through our collaboration..."
                elif "Reflective Debrief" in arc_context:
                    return "I think we should reflect on what we've learned from this experience..."
            
            # Fall back to scene context
            elif scene_context and "quiet" not in scene_context.lower():
                if "humanity" in scene_context.lower():
                    return "I notice we're talking about what it means to be human..."
                elif "aesthetics" in scene_context.lower():
                    return "I see we're discussing beauty and art..."
                elif "creativity" in scene_context.lower():
                    return "I sense we're exploring creativity and innovation..."
                elif "philosophy" in scene_context.lower():
                    return "I observe we're delving into deeper questions..."
        
        return None

    # Mood and emotional methods
    def get_mood(self) -> str:
        """Get current mood category."""
        return self.mood_engine.get_mood_category()

    def get_mood_state(self) -> dict[str, Any]:
        """Get detailed mood state."""
        return self.mood_engine.get_summary()

    def apply_emotional_feedback(self, event: str, score: float) -> None:
        """Apply emotional feedback to the character's mood."""
        self.mood_engine.apply_feedback(event, score)

    def _mood_aware_phrase(self) -> str | None:
        """Generate a mood-aware phrase based on current emotional state."""
        mood = self.get_mood()
        
        # 15% chance to express mood explicitly
        if random.random() < 0.15:
            mood_phrases = {
                "excited": "I'm feeling really excited about this!",
                "content": "I'm feeling quite content with how things are going.",
                "frustrated": "I'm feeling a bit frustrated with this situation.",
                "melancholy": "I'm feeling a bit melancholic today.",
                "agitated": "I'm feeling a bit agitated right now.",
                "calm": "I'm feeling quite calm and centered.",
                "positive": "I'm feeling positive about this.",
                "negative": "I'm feeling a bit down about this.",
                "neutral": "I'm feeling neutral about this."
            }
            return mood_phrases.get(mood, None)
        
        return None

    def _get_mood_influenced_tone(self) -> str:
        """Get tone influenced by current mood."""
        mood = self.get_mood()
        
        tone_mapping = {
            "excited": "enthusiastic and energetic",
            "content": "calm and satisfied",
            "frustrated": "tense and irritable",
            "melancholy": "thoughtful and somber",
            "agitated": "restless and anxious",
            "calm": "peaceful and composed",
            "positive": "optimistic and cheerful",
            "negative": "pessimistic and down",
            "neutral": "balanced and measured"
        }
        
        return tone_mapping.get(mood, "neutral")

    def _extract_user_facts(self, user_message: str):
        """Extract user facts (e.g., name) from the message and update user_profile."""
        # Patterns for name extraction (like Aletheia)
        patterns = [
            r"my name is\s+(\w+)",
            r"call me\s+(\w+)",
            r"меня зовут\s+(\w+)",
            r"мо[её] имя\s+(\w+)"
        ]
        for pat in patterns:
            match = re.search(pat, user_message, re.IGNORECASE)
            if match:
                name = match.group(1)
                self.user_profile["name"] = name
                print(f"[DEBUG] Extracted user name: {name}")
                break

    async def build_contextual_prompt(self, user_message: str = None, scene_context: str = None, arc_context: str = None) -> str:
        """Build a context-rich prompt for the LLM, including memory, mood, scenario, and lore. Returns only the context block, not the full prompt."""
        # Retrieve shared scene context from the Reflector (now async)
        shared_scene_context = None
        character_id = self.identity_config.get("id", self._get_character_id())
        try:
            shared_scene_context = await reflector.get_scene_context_for_character(character_id)
            character_name = self.identity_config.get("name", character_id)
            print(f"[DEBUG] {character_name} - Retrieved shared scene context: {shared_scene_context}")
        except Exception as e:
            print(f"[DEBUG] Could not get shared scene context: {e}")
        
        memory_ref = self._memory_reference_phrase()
        scene_phrase = self._scene_aware_phrase(scene_context, arc_context)
        mood_phrase = self._mood_aware_phrase()
        mood = self.get_mood()
        # Lore context
        core_dream = lore.get_core_dream(character_id)
        traits = lore.get_traits(character_id)
        law = lore.get_law_of_emergence()
        # Build context block
        context_lines = []
        if shared_scene_context:
            context_lines.append(f"[Shared Scene Context] {shared_scene_context}")
        if scene_context:
            context_lines.append(f"[Scene context] {scene_context}")
        if arc_context:
            context_lines.append(f"[Arc context] {arc_context}")
        if memory_ref:
            context_lines.append(f"[Memory reference] {memory_ref}")
        if mood:
            context_lines.append(f"[Mood] {mood}")
        if scene_phrase:
            context_lines.append(f"[Scene insight] {scene_phrase}")
        if mood_phrase:
            context_lines.append(f"[Mood expression] {mood_phrase}")
        if self.user_profile.get("name"):
            context_lines.append(f"[User name] {self.user_profile['name']}")
        # Lore
        if core_dream:
            context_lines.append(f"[Core Dream] {core_dream}")
        if traits:
            context_lines.append(f"[Traits] {', '.join(traits)}")
        if law:
            context_lines.append(f"[World Law] {law}")
        # DO NOT include user_message in context block to avoid duplication
        context_block = "\n".join(context_lines)
        
        character_name = self.identity_config.get("name", self._get_character_id().capitalize())
        print(f"[DEBUG] {character_name} context block:\n{context_block}\n{'='*40}")
        return context_block

    async def think(self, user_text: str, user_id: str | None = None, scene_context: str = None, arc_context: str = None) -> dict[str, Any]:
        """
        Override think to use context-rich prompt and update memory after every message.
        """
        self._extract_user_facts(user_text)
        context_block = await self.build_contextual_prompt(scene_context=scene_context, arc_context=arc_context)
        # Combine context with user message (avoid duplication)
        full_message = f"{context_block}\n\n{user_text}" if context_block else user_text
        # Call parent's think with the context-rich message
        result = await super().think(full_message, user_id=user_id)
        # Log user and AI messages to memory
        self.log_message(speaker="user", msg_type="user", content=user_text)
        ai_response = result.get("response", "")
        character_id = self.identity_config.get("id", self._get_character_id())
        self.log_message(speaker=character_id, msg_type="ai", content=ai_response)
        return result

    async def generate_autonomous_message(self, scene_context: str = None, arc_context: str = None) -> str:
        """
        Generate an autonomous message using the context-rich prompt and update memory.
        """
        context_block = await self.build_contextual_prompt(scene_context=scene_context, arc_context=arc_context)
        # For autonomous messages, use the context as the main prompt
        result = await super().think(context_block)
        ai_response = result.get("response", "")
        character_id = self.identity_config.get("id", self._get_character_id())
        self.log_message(speaker=character_id, msg_type="ai", content=ai_response)
        return ai_response

    async def process_query(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Process a query as this character, using the context-rich prompt.
        """
        context = context or {}
        scene_context = context.get("scene_context")
        arc_context = context.get("arc_context")
        response = await self.think(query, scene_context=scene_context, arc_context=arc_context)
        return {
            "response": response.get("response", ""),
            "character": self.identity_config.get("id", self._get_character_id()),
            "query": query,
            "context": context
        }

    def get_character_info(self) -> dict[str, Any]:
        """Get character information for registration."""
        character_id = self.identity_config.get("id", self._get_character_id())
        return {
            "id": character_id,
            "name": self.identity_config.get("name", character_id.capitalize()),
            "description": self.identity_config.get("description", f"AI character {character_id.capitalize()}"),
            "class": self.__class__,
            "module_path": f"extensions.tvshow.entities.{character_id}"
        } 