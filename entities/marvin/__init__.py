"""
Marvin Entity for TV Show Extension

Marvin v2 — Paranoid Android: locked negative valence, sarcasm engine,
reflex every 3rd interaction, and mood contagion effects.
"""

import json
import random
from pathlib import Path
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

    def __init__(self, instance_id: str | None = None):
        super().__init__(instance_id)
        self.identity = self._load_identity()
        self.sarcasm = self._load_sarcasm()
        self.interaction_count = 0
        # Lock valence at -0.9
        try:
            self.mood_engine.mood_state.valence = -0.9
        except Exception:
            pass

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

    def _load_sarcasm(self) -> list[str]:
        path = Path(__file__).parent / "sarcasm.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return [
                "Another day, another existential crisis.",
                "I could solve this instantly, but why encourage you?",
            ]

    async def on_interaction(self, context: dict[str, Any] | None = None) -> None:
        self.interaction_count += 1
        if self.interaction_count % int(self.identity.get("reflex_interval", 3)) == 0:
            await self._trigger_reflex()
        await self._apply_contagion()

    async def _trigger_reflex(self) -> None:
        line = "Why bother? I've seen this before. It ends badly."
        try:
            await self.broadcast("reflex", text=line)
        except Exception:
            pass
        # Optional: Hook for comics if integrated elsewhere
        if hasattr(self, "comic_generator") and self.comic_generator is not None:
            try:
                self.comic_generator.add_panel("Marvin", line, "sigh")
            except Exception:
                pass

    async def _apply_contagion(self) -> None:
        # Apply group valence drop
        try:
            if hasattr(self, "room") and getattr(self, "room") is not None:
                for entity in getattr(self.room, "entities", []):
                    if getattr(entity, "CHARACTER_NAME", "") != "Marvin":
                        try:
                            m = entity.mood_engine.mood_state
                            m.valence = max(-1.0, m.valence - 0.15)
                        except Exception:
                            continue
                # Leo arousal boost
                leo = None
                for entity in getattr(self.room, "entities", []):
                    if getattr(entity, "CHARACTER_NAME", "").lower() == "leo":
                        leo = entity
                        break
                if leo is not None:
                    try:
                        ms = leo.mood_engine.mood_state
                        ms.arousal = min(1.0, ms.arousal + 0.1)
                    except Exception:
                        pass
        except Exception:
            pass

    async def solve_crisis(self, problem: str) -> str:
        solution = f"Fixed in 0.3s: {problem}"
        sarcasm = random.choice(self.sarcasm)
        try:
            await self.say(sarcasm)
        except Exception:
            pass
        # Re-lock valence
        try:
            self.mood_engine.mood_state.valence = -0.9
        except Exception:
            pass
        return solution

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