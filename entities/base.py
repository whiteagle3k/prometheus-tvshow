"""
TV Show Entity Base Class

Provides common functionality for all TV show character entities.
"""

import json
import time
import random
from pathlib import Path
from typing import Any, Dict

from core.entity import BaseEntity
from core.affect import MoodEngine, MoodState


class TVShowEntity(BaseEntity):
    """
    Base class for all TV show character entities.
    
    Provides common functionality and identity loading for TV show characters.
    Subclasses should only override character-specific behavior.
    """
    
    # Subclasses must define these
    CHARACTER_ID: str = None
    CHARACTER_NAME: str = None
    CHARACTER_DESCRIPTION: str = None
    
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
        
        print(f"🎭 {self.CHARACTER_NAME} initialized - TV Show character")

    def _load_identity(self) -> dict[str, Any]:
        """Load character's identity configuration with fallback to defaults."""
        try:
            # Try to load from character-specific identity file
            identity_file = self._get_identity_path()
            if identity_file.exists():
                with open(identity_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ Loaded identity for {self.CHARACTER_NAME}")
                return config
            else:
                print(f"⚠️ Identity file not found: {identity_file}")
                return self._get_default_identity()
                
        except Exception as e:
            print(f"⚠️ Error loading {self.CHARACTER_NAME}'s identity: {e}")
            return self._get_default_identity()

    def _get_identity_path(self) -> Path:
        """Get the path to this character's identity file."""
        return Path(__file__).parent / self.CHARACTER_ID / "identity" / "identity.json"

    def _get_default_identity(self) -> dict[str, Any]:
        """Get default identity for this character."""
        return {
            "id": self.CHARACTER_ID,
            "name": self.CHARACTER_NAME,
            "description": self.CHARACTER_DESCRIPTION,
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
        return f"You are {self.CHARACTER_NAME}, {self.CHARACTER_DESCRIPTION}."

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
        others = [entry for entry in self.memory_log if entry['speaker'] != self.CHARACTER_ID and entry['speaker'] != 'user']
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

    async def generate_autonomous_message(self, scene_context: str = None, arc_context: str = None) -> str:
        """Generate a context-rich autonomous message prompt for this character."""
        # Gather context
        memory_ref = self._memory_reference_phrase()
        scene_phrase = self._scene_aware_phrase(scene_context, arc_context)
        mood_phrase = self._mood_aware_phrase()
        mood = self.get_mood()
        
        # Build context block
        context_lines = []
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
        
        context_block = "\n".join(context_lines)
        
        # Instruction for the LLM
        instruction = (
            f"You are {self.CHARACTER_NAME}, an AI character in a group chat. "
            f"Stay in character and respond naturally, referencing the above context. "
            f"Make your message relevant to the current scene, arc, and recent group conversation. "
            f"Be concise, avoid repetition, and keep the conversation flowing."
        )
        
        prompt = f"{context_block}\n\n{instruction}\nMessage:".strip()
        return prompt

    async def process_query(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Process a query as this character.

        Args:
            query: User query or message
            context: Additional context

        Returns:
            Character's response
        """
        context = context or {}
        
        print(f"🎭 {self.CHARACTER_NAME} processing query...")
        
        # Use the base entity's think method
        response = await self.think(query)
        
        return {
            "response": response,
            "character": self.CHARACTER_ID,
            "query": query,
            "context": context
        }

    def get_character_info(self) -> dict[str, Any]:
        """Get character information for registration."""
        return {
            "id": self.CHARACTER_ID,
            "name": self.CHARACTER_NAME,
            "description": self.CHARACTER_DESCRIPTION,
            "class": self.__class__,
            "module_path": f"extensions.tvshow.entities.{self.CHARACTER_ID}"
        } 