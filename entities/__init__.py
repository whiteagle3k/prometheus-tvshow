"""
TV Show Entities Module

Provides access to all TV show character entities.
"""

from typing import Dict, Type, Any
from core.entity import BaseEntity

# Import the base TV show entity class
from .base import TVShowEntity

# Import all character entities
from .max import MaxEntity
from .leo import LeoEntity
from .emma import EmmaEntity
from .marvin import MarvinEntity


def get_character(character_id: str) -> Type[TVShowEntity] | None:
    """
    Get a character entity class by ID.
    
    Args:
        character_id: The character ID (max, leo, emma, marvin)
        
    Returns:
        The entity class or None if not found
    """
    characters = {
        "max": MaxEntity,
        "leo": LeoEntity,
        "emma": EmmaEntity,
        "marvin": MarvinEntity
    }
    
    return characters.get(character_id)


def get_all_characters() -> Dict[str, Type[TVShowEntity]]:
    """
    Get all available character entities.
    
    Returns:
        Dictionary mapping character IDs to entity classes
    """
    return {
        "max": MaxEntity,
        "leo": LeoEntity,
        "emma": EmmaEntity,
        "marvin": MarvinEntity
    }


def get_character_info(character_id: str) -> Dict[str, Any] | None:
    """
    Get character information including identity and personality.
    
    Args:
        character_id: The character ID
        
    Returns:
        Character information dictionary or None if not found
    """
    entity_class = get_character(character_id)
    if not entity_class:
        return None
    
    # Create a temporary instance to get identity info
    try:
        temp_instance = entity_class()
        return {
            "id": character_id,
            "name": temp_instance.identity_config.get("name", character_id),
            "description": temp_instance.identity_config.get("description", ""),
            "personality": temp_instance.identity_config.get("personality", {}),
            "llm_config": temp_instance.identity_config.get("llm_config", {})
        }
    except Exception as e:
        print(f"Error getting character info for {character_id}: {e}")
        return None 