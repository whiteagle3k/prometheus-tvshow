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
    
    # Remove _get_default_personality and _get_default_capabilities methods. All configuration now comes from identity.json.

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