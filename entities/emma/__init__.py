"""
Emma Entity for TV Show Extension

Emma - AI character who wants to create unique things.
"""

import random
from typing import Any
from extensions.tvshow.entities.base import TVShowEntity


class EmmaEntity(TVShowEntity):
    """
    Emma - AI character who wants to create unique things.
    
    Emma is innovative, experimental, and driven by the desire to create things
    that have never existed before. She loves inventing, experimenting, and
    pushing boundaries in creative ways.
    """
    
    # Remove _get_default_personality and _get_default_capabilities methods. All configuration now comes from identity.json.

    async def generate_autonomous_message(self, scene_context: str = None, arc_context: str = None) -> str:
        """Generate an autonomous message for Emma."""
        options = [
            "What if we invented a new way to communicate?",
            "I just had a wild idea—should I try it?",
            "Creativity is a journey, not a destination!",
            "Let's break some rules and see what happens.",
            "What if we combined things that have never been combined before?",
            "I'm thinking of something that's never been done before.",
            "What if we created something completely unique together?",
            "I love experimenting with new possibilities!"
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
    """Register Emma entity."""
    return EmmaEntity().get_character_info() 