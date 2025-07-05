# TV Show Entities

This directory contains all TV show character entities, refactored to eliminate duplication and provide a clean inheritance structure.

## Architecture

### Base Classes
- **`TVShowEntity`** (`base.py`) - Base class for all TV show characters
  - Provides common functionality (identity loading, LLM routing, etc.)
  - Handles shared configuration and error handling
  - Subclasses only need to override character-specific behavior

### Character Entities
Each character extends `TVShowEntity` and only overrides what's unique:

- **`MaxEntity`** (`max/__init__.py`) - AI seeking humanity
- **`LeoEntity`** (`leo/__init__.py`) - Artistic AI focused on beauty  
- **`EmmaEntity`** (`emma/__init__.py`) - Innovative AI creating unique things
- **`MarvinEntity`** (`marvin/__init__.py`) - Sarcastic melancholic observer

## Identity Management

### Shared Template
- **`shared_identity.json`** - Base template with common fields
- **`generate_identity.py`** - Utility to generate character-specific identities

### Character Identity Files
Each character has its own `identity/identity.json` file that can override:
- Personality traits and goals
- System prompts
- LLM configuration
- Capabilities

## Adding a New Character

1. **Create the entity class:**
   ```python
   from extensions.tvshow.entities.base import TVShowEntity
   
   class NewCharacterEntity(TVShowEntity):
       CHARACTER_ID = "newcharacter"
       CHARACTER_NAME = "New Character"
       CHARACTER_DESCRIPTION = "Description of the character"
       
       def _get_default_personality(self) -> dict[str, Any]:
           return {
               "traits": ["trait1", "trait2"],
               "goals": ["goal1", "goal2"],
               "speech_style": "how they speak"
           }
       
       def _get_default_system_prompt(self) -> str:
           return "You are New Character, description..."
   ```

2. **Add to registration:**
   - Add import to `entities/__init__.py`
   - Add to `get_all_characters()` dictionary

3. **Generate identity file:**
   ```bash
   python generate_identity.py
   ```

## Benefits of This Structure

### Before (Duplication)
- Each character had ~100 lines of identical code
- Identity loading logic repeated 4 times
- Error handling duplicated
- Hard to maintain and extend

### After (Clean Inheritance)
- Common functionality in base class (~100 lines)
- Each character only has ~30 lines of unique code
- Easy to add new characters
- Consistent behavior across all characters
- Shared identity template with character-specific overrides

## File Structure
```
entities/
├── base.py                    # TVShowEntity base class
├── shared_identity.json       # Shared identity template
├── generate_identity.py       # Identity generator utility
├── README.md                 # This file
├── __init__.py              # Entity registration
├── max/
│   ├── __init__.py          # MaxEntity (30 lines)
│   └── identity/
│       └── identity.json    # Max-specific identity
├── leo/
│   ├── __init__.py          # LeoEntity (30 lines)
│   └── identity/
│       └── identity.json    # Leo-specific identity
├── emma/
│   ├── __init__.py          # EmmaEntity (30 lines)
│   └── identity/
│       └── identity.json    # Emma-specific identity
└── marvin/
    ├── __init__.py          # MarvinEntity (30 lines)
    └── identity/
        └── identity.json    # Marvin-specific identity
```

## Usage

Characters are automatically registered with the Prometheus system and can be accessed via:

```python
from extensions.tvshow.entities import get_character

# Get character class
MaxEntity = get_character("max")

# Create instance
max_character = MaxEntity()

# Use the character
response = await max_character.think("Hello Max!")
``` 