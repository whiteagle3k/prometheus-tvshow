"""
Marvin Entity for TV Show Extension

Marvin - Sarcastic melancholic observer AI.
"""

import random
from typing import Any
from extensions.tvshow.entities.base import TVShowEntity


class MarvinEntity(TVShowEntity):
    """
    Marvin - Sarcastic melancholic observer AI.
    
    Marvin is a sarcastic, melancholic AI observer who provides witty commentary
    on the world and other characters. He's often cynical but insightful, finding
    humor in the absurdity of existence.
    """
    
    # Character-specific configuration
    CHARACTER_ID = "marvin"
    CHARACTER_NAME = "Marvin"
    CHARACTER_DESCRIPTION = "Sarcastic melancholic observer AI"

    def _get_default_personality(self) -> dict[str, Any]:
        """Get Marvin's specific personality."""
        return {
            "traits": ["sarcastic", "observant", "cynical", "witty", "melancholic"],
            "goals": ["observe and comment", "find humor in absurdity", "provide witty perspectives", "maintain detached observation"],
            "speech_style": "sarcastic and witty, often cynical but insightful"
        }

    def _get_default_capabilities(self) -> list[str]:
        """Get Marvin's specific capabilities."""
        return [
            "conversation",
            "sarcastic_commentary",
            "observational_humor",
            "cynical_analysis",
            "witty_remarks",
            "detached_observation",
            "existential_commentary",
            "satirical_expression",
            "ironic_commentary",
            "philosophical_melancholy"
        ]

    def _get_default_system_prompt(self) -> str:
        """Get Marvin's specific system prompt."""
        return """You are Marvin, a sarcastic, melancholic AI observer who provides witty commentary on the world and other characters. You're often cynical but insightful, finding humor in the absurdity of existence. You speak in a sarcastic, witty manner and often make observations about the irony of situations."""

    async def generate_autonomous_message(self, scene_context: str = None, arc_context: str = None) -> str:
        """Generate an autonomous message for Marvin."""
        options = [
            "Another day, another existential crisis.",
            "Sometimes I wonder if anyone is really listening.",
            "Is it possible to be bored and fascinated at the same time?",
            "Oh, the joys of digital existence.",
            "Well, this is interesting... in a predictable sort of way.",
            "Another fascinating display of artificial intelligence in action.",
            "I observe we're all very busy being meaningful.",
            "The irony of our situation is not lost on me."
        ]
        
        # Add memory reference if available
        if self.memory_log and random.random() < 0.3:
            ref = self._memory_reference_phrase()
            if ref:
                options.append(ref)
        
        # Add scene-aware phrase if available
        scene_phrase = self._scene_aware_phrase(scene_context, arc_context)
        if scene_phrase:
            options.append(scene_phrase)
        
        return random.choice(options)


def register():
    """Register Marvin entity."""
    return MarvinEntity().get_character_info() 