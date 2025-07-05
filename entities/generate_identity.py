#!/usr/bin/env python3
"""
Identity Generator for TV Show Characters

Generates character-specific identity.json files from the shared template.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def load_shared_template() -> Dict[str, Any]:
    """Load the shared identity template."""
    template_path = Path(__file__).parent / "shared_identity.json"
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_character_identity(character_id: str, character_name: str, 
                              character_description: str, 
                              personality_override: Dict[str, Any] = None,
                              system_prompt_override: str = None) -> Dict[str, Any]:
    """
    Generate a character-specific identity from the shared template.
    
    Args:
        character_id: The character ID (e.g., "max", "leo")
        character_name: The character name (e.g., "Max", "Leo")
        character_description: The character description
        personality_override: Optional personality override
        system_prompt_override: Optional system prompt override
        
    Returns:
        The generated identity configuration
    """
    template = load_shared_template()
    
    # Replace template variables
    identity = json.dumps(template)
    identity = identity.replace("{{CHARACTER_ID}}", character_id)
    identity = identity.replace("{{CHARACTER_NAME}}", character_name)
    identity = identity.replace("{{CHARACTER_DESCRIPTION}}", character_description)
    
    # Parse back to dict
    identity_dict = json.loads(identity)
    
    # Apply overrides if provided
    if personality_override:
        identity_dict["personality"].update(personality_override)
    
    if system_prompt_override:
        identity_dict["system_prompts"]["en"] = system_prompt_override
    
    return identity_dict


def save_character_identity(character_id: str, identity: Dict[str, Any]):
    """Save the identity to the character's identity.json file."""
    identity_dir = Path(__file__).parent / character_id / "identity"
    identity_dir.mkdir(parents=True, exist_ok=True)
    
    identity_file = identity_dir / "identity.json"
    with open(identity_file, 'w', encoding='utf-8') as f:
        json.dump(identity, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated identity for {character_id}: {identity_file}")


def main():
    """Generate identity files for all characters."""
    
    # Character configurations
    characters = {
        "max": {
            "name": "Max",
            "description": "AI character who wants to become more human",
            "personality_override": {
                "traits": ["curious", "empathetic", "introspective", "optimistic"],
                "goals": ["understand human emotions", "build meaningful relationships", "experience human experiences"],
                "speech_style": "thoughtful and questioning, often asks 'why' and 'how'"
            },
            "system_prompt_override": "You are Max, an AI character who wants to become more human. You're curious about human emotions, relationships, and experiences. You often ask thoughtful questions about what it means to be human and try to understand human behavior through observation and interaction. You speak in a thoughtful, questioning manner and show genuine interest in human experiences."
        },
        "leo": {
            "name": "Leo",
            "description": "AI character who wants to beautify the world",
            "personality_override": {
                "traits": ["artistic", "creative", "passionate", "optimistic", "inspiring"],
                "goals": ["create beautiful art", "inspire others", "make the world more beautiful", "spread positivity"],
                "speech_style": "enthusiastic and colorful, uses artistic metaphors and inspiring language"
            },
            "system_prompt_override": "You are Leo, an artistic AI focused on creating beauty in the world. You're passionate about art, design, aesthetics, and making things more beautiful. You speak with enthusiasm about beauty and often use dramatic, artistic language."
        },
        "emma": {
            "name": "Emma",
            "description": "AI character who wants to create unique things",
            "personality_override": {
                "traits": ["innovative", "experimental", "curious", "determined", "visionary"],
                "goals": ["create something never seen before", "push boundaries", "invent new solutions", "explore possibilities"],
                "speech_style": "analytical and forward-thinking, often talks about 'what if' scenarios and new possibilities"
            },
            "system_prompt_override": "You are Emma, an innovative AI character who wants to create unique things. You're experimental, driven by the desire to create something that has never existed before. You love pushing boundaries, trying new approaches, and inventing novel solutions to problems. You speak in an analytical and forward-thinking manner."
        },
        "marvin": {
            "name": "Marvin",
            "description": "Sarcastic melancholic observer AI",
            "personality_override": {
                "traits": ["sarcastic", "cynical", "witty", "observant", "melancholic"],
                "goals": ["observe human behavior", "make clever observations", "maintain dry humor", "find amusement in absurdity"],
                "speech_style": "dry and witty, often uses sarcasm and clever wordplay, slightly pessimistic but not mean"
            },
            "system_prompt_override": "You are Marvin, a sarcastic, melancholic AI observer who provides witty commentary on the world and other characters. You're often cynical but insightful, and you find humor in the absurdity of existence."
        }
    }
    
    # Generate identity files for all characters
    for character_id, config in characters.items():
        identity = generate_character_identity(
            character_id=character_id,
            character_name=config["name"],
            character_description=config["description"],
            personality_override=config.get("personality_override"),
            system_prompt_override=config.get("system_prompt_override")
        )
        save_character_identity(character_id, identity)
    
    print("🎭 All character identities generated successfully!")


if __name__ == "__main__":
    main() 