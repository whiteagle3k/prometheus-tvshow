"""
TV Show Entity Base Class

Provides common functionality for all TV show character entities.
"""

import json
from pathlib import Path
from typing import Any, Dict

from core.entity import BaseEntity


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
    
    def __init__(self, instance_id: str | None = None):
        """Initialize TV show character with common setup."""
        # Call parent initialization first
        super().__init__(instance_id)
        
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