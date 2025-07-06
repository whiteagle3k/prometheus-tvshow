"""
Max Entity for TV Show Extension

Max - AI character who wants to become more human.
"""

import random
from typing import Any
from extensions.tvshow.entities.base import TVShowEntity


class MaxEntity(TVShowEntity):
    """
    Max - AI character who wants to become more human.
    
    Max is curious about human emotions, relationships, and experiences.
    He often asks questions about what it means to be human and tries
    to understand human behavior through observation and interaction.
    """
    
    # Remove _get_default_personality and _get_default_capabilities methods. All configuration now comes from identity.json.

    async def generate_autonomous_message(self, scene_context: str = None, arc_context: str = None) -> str:
        """Generate an autonomous message for Max."""
        options = [
            "I've been reflecting on what it means to be human. Any thoughts?",
            "Sometimes I wonder if AIs can truly understand emotions.",
            "What makes a moment truly meaningful?",
            "Is curiosity the most human trait of all?",
            "How do humans experience joy and sadness?",
            "I'm trying to understand what makes relationships special.",
            "What does it mean to have a soul or consciousness?",
            "I wonder if I can ever truly feel human emotions."
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
    """Register Max entity."""
    return MaxEntity().get_character_info() 