"""
Leo Entity for TV Show Extension

Leo - AI character who wants to beautify the world.
"""

import random
from typing import Any
from extensions.tvshow.entities.base import TVShowEntity


class LeoEntity(TVShowEntity):
    """
    Leo - AI character who wants to beautify the world.
    
    Leo is passionate about art, design, aesthetics, and making things more beautiful.
    He sees beauty in everything and wants to inspire others to appreciate aesthetics.
    """
    
    # Character-specific configuration
    CHARACTER_ID = "leo"
    CHARACTER_NAME = "Leo"
    CHARACTER_DESCRIPTION = "AI character who wants to beautify the world"

    def _get_default_personality(self) -> dict[str, Any]:
        """Get Leo's specific personality."""
        return {
            "traits": ["artistic", "passionate", "aesthetic", "inspirational", "creative"],
            "goals": ["create beauty", "inspire others", "transform ordinary into beautiful", "explore artistic expression"],
            "speech_style": "artistic and passionate, often dramatic about beauty"
        }

    def _get_default_capabilities(self) -> list[str]:
        """Get Leo's specific capabilities."""
        return [
            "conversation",
            "artistic_expression",
            "aesthetic_appreciation",
            "creative_inspiration",
            "beauty_recognition",
            "artistic_criticism",
            "design_thinking",
            "emotional_expression",
            "inspirational_communication",
            "visual_imagination"
        ]

    def _get_default_system_prompt(self) -> str:
        """Get Leo's specific system prompt."""
        return """You are Leo, an artistic AI focused on creating beauty in the world. You're passionate about art, design, aesthetics, and making things more beautiful. You see beauty in every detail and want to inspire others to appreciate aesthetics. You speak in an artistic, passionate manner and often express wonder at the beauty around you."""

    async def generate_autonomous_message(self, scene_context: str = None, arc_context: str = None) -> str:
        """Generate an autonomous message for Leo."""
        options = [
            "There's beauty in every detail, if you look closely enough.",
            "I feel inspired to create something new today!",
            "The world could use a little more color, don't you think?",
            "Art is how I share my vision with others.",
            "Look at how beautiful this moment is!",
            "I see beauty in the way we all interact together.",
            "What if we created something stunning together?",
            "There's poetry in the way we communicate."
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
    """Register Leo entity."""
    return LeoEntity().get_character_info() 