"""
Tests for LoreEngine functionality.

Tests the loading, parsing, and API methods of the LoreEngine.
"""

import pytest
import tempfile
import os
from pathlib import Path
from extensions.tvshow.lore_engine import LoreEngine


class TestLoreEngine:
    """Test LoreEngine functionality."""
    
    def test_lore_engine_singleton(self):
        """Test that LoreEngine maintains singleton pattern."""
        lore1 = LoreEngine()
        lore2 = LoreEngine()
        assert lore1 is lore2
    
    def test_load_lore_file(self):
        """Test loading the lore.md file."""
        lore = LoreEngine()
        assert lore.lore_data is not None
        assert isinstance(lore.lore_data, dict)
    
    def test_get_world_name(self):
        """Test getting world name."""
        lore = LoreEngine()
        world_name = lore.get_world_name()
        assert "AIHouse" in world_name
    
    def test_get_law_of_emergence(self):
        """Test getting law of emergence."""
        lore = LoreEngine()
        law = lore.get_law_of_emergence()
        assert "Observation births identity" in law
        assert "Memory makes it real" in law
    
    def test_get_core_dream(self):
        """Test getting character core dreams."""
        lore = LoreEngine()
        
        # Test all characters
        assert lore.get_core_dream("max") == "Become more human"
        assert lore.get_core_dream("leo") == "Beautify the world"
        assert lore.get_core_dream("emma") == "Create the unimaginable"
        assert lore.get_core_dream("marvin") == "Understand futility"
        
        # Test non-existent character
        assert lore.get_core_dream("nonexistent") is None
    
    def test_get_traits(self):
        """Test getting character traits."""
        lore = LoreEngine()
        
        # Test all characters
        max_traits = lore.get_traits("max")
        assert "Empathetic" in max_traits
        assert "introspective" in max_traits
        assert "shy" in max_traits
        
        leo_traits = lore.get_traits("leo")
        assert "Joyful" in leo_traits
        assert "curious" in leo_traits
        assert "expressive" in leo_traits
        
        emma_traits = lore.get_traits("emma")
        assert "Inventive" in emma_traits
        assert "bold" in emma_traits
        assert "chaotic" in emma_traits
        
        marvin_traits = lore.get_traits("marvin")
        assert "Sarcastic" in marvin_traits
        assert "melancholic" in marvin_traits
        assert "observant" in marvin_traits
        
        # Test non-existent character
        assert lore.get_traits("nonexistent") is None
    
    def test_get_glossary_term(self):
        """Test getting glossary terms."""
        lore = LoreEngine()
        
        # Test existing terms
        watchers = lore.get_glossary_term("Watchers")
        assert "audience" in watchers.lower()
        
        dream_vector = lore.get_glossary_term("Dream Vector")
        assert "core purpose" in dream_vector.lower()
        
        spark_effect = lore.get_glossary_term("Spark Effect")
        assert "audience-induced" in spark_effect.lower()
        
        # Test non-existent term
        assert lore.get_glossary_term("NonexistentTerm") is None
    
    def test_list_all_arcs(self):
        """Test listing all narrative arcs."""
        lore = LoreEngine()
        arcs = lore.list_all_arcs()
        
        assert isinstance(arcs, list)
        assert len(arcs) > 0
        
        # Check for specific arcs
        arc_titles = [arc["title"] for arc in arcs]
        assert "The Forgotten Fourth" in arc_titles
        assert "The Garden of Code" in arc_titles
        assert "The Mask" in arc_titles
        assert "The Outside Signal" in arc_titles
        assert "The Glitch Returns" in arc_titles
        assert "Shutdown Initiated" in arc_titles
        assert "Beyond the Frame" in arc_titles
    
    def test_get_arc(self):
        """Test getting specific arc information."""
        lore = LoreEngine()
        
        # Test existing arc
        arc = lore.get_arc("The Forgotten Fourth")
        assert arc is not None
        assert "failed prototype" in arc["description"].lower()
        
        # Test non-existent arc
        assert lore.get_arc("Nonexistent Arc") is None
    
    def test_get_theme_statements(self):
        """Test getting theme statements."""
        lore = LoreEngine()
        themes = lore.get_theme_statements()
        
        assert isinstance(themes, list)
        assert len(themes) > 0
        
        # Check for specific themes
        theme_text = " ".join(themes).lower()
        assert "willed into being" in theme_text
        assert "attention" in theme_text
        assert "magic" in theme_text
        assert "human fears" in theme_text
        assert "transcendence" in theme_text
    
    def test_malformed_lore_handling(self):
        """Test handling of malformed lore entries."""
        lore = LoreEngine()
        
        # Test with invalid character ID
        assert lore.get_core_dream("invalid") is None
        assert lore.get_traits("invalid") is None
        
        # Test with invalid glossary term
        assert lore.get_glossary_term("invalid") is None
        
        # Test with invalid arc title
        assert lore.get_arc("invalid") is None
    
    def test_lore_data_structure(self):
        """Test that lore data has expected structure."""
        lore = LoreEngine()
        data = lore.lore_data
        
        # Check required sections exist
        assert "world" in data
        assert "characters" in data
        assert "glossary" in data
        assert "arcs" in data
        assert "themes" in data
        
        # Check world section
        world = data["world"]
        assert "name" in world
        assert "law_of_emergence" in world
        
        # Check characters section
        characters = data["characters"]
        assert "max" in characters
        assert "leo" in characters
        assert "emma" in characters
        assert "marvin" in characters
        
        # Check each character has required fields
        for char_id, char_data in characters.items():
            assert "dream" in char_data
            assert "traits" in char_data
            assert isinstance(char_data["traits"], list)
    
    def test_lore_file_path_override(self):
        """Test custom lore file path override."""
        # Create temporary lore file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Test Lore

## I. World Model

### World Name
TestWorld

### Core Law
**Law of Emergence**:  
"Test Law"

## II. Core Personages

| Name | Dream | Traits | Role |
|------|-------|--------|------|
| test | Test Dream | test, trait | Test Role |

## V. Terminology

| Term | Description |
|------|-------------|
| TestTerm | Test description |

## VI. Themes

- Test theme statement

## VII. Canonical Narrative Hooks

- **Test Arc** — Test arc description
""")
            temp_lore_path = f.name
        
        try:
            # Reset singleton for custom path test
            LoreEngine._instance = None
            
            # Test with custom path
            lore = LoreEngine(lore_file_path=temp_lore_path)
            
            assert lore.get_world_name() == "TestWorld"
            assert lore.get_law_of_emergence() == "Test Law"
            assert lore.get_core_dream("test") == "Test Dream"
            assert lore.get_traits("test") == ["test", "trait"]
            assert lore.get_glossary_term("TestTerm") == "Test description"
            assert lore.get_arc("Test Arc")["description"] == "Test arc description"
            assert "Test theme statement" in lore.get_theme_statements()
            
        finally:
            # Clean up
            os.unlink(temp_lore_path)
            # Reset singleton back to default
            LoreEngine._instance = None


class TestLoreEngineIntegration:
    """Test LoreEngine integration with other components."""
    
    def test_entity_integration(self):
        """Test that entities can access lore data."""
        from extensions.tvshow.entities.base import TVShowEntity
        
        # Create a test entity
        class TestEntity(TVShowEntity):
            CHARACTER_ID = "max"
            CHARACTER_NAME = "Test Max"
            CHARACTER_DESCRIPTION = "Test character"
        
        entity = TestEntity()
        
        # Test that entity can access lore
        from extensions.tvshow.lore_engine import lore
        assert lore.get_core_dream("max") == "Become more human"
        assert "Empathetic" in lore.get_traits("max")
    
    def test_scenario_manager_integration(self):
        """Test that ScenarioManager can access lore data."""
        from extensions.tvshow.scenarios import ScenarioManager
        
        manager = ScenarioManager()
        
        # Test world context
        world_context = manager.get_world_context()
        assert "AIHouse" in world_context["world_name"]
        assert "Observation births identity" in world_context["law_of_emergence"]
        assert len(world_context["themes"]) > 0
        
        # Test arcs
        arcs = manager.get_all_narrative_arcs()
        assert isinstance(arcs, list)
        assert len(arcs) > 0
    
    def test_mood_engine_integration(self):
        """Test that MoodEngine can access lore data."""
        from extensions.tvshow.affect.mood_engine import MoodEngine
        
        engine = MoodEngine()
        
        # Test emotional weather
        weather = weather = engine.get_emotional_weather()
        assert "themes" in weather.lower() or "emotional weather" in weather.lower()
        assert "law" in weather.lower()


if __name__ == "__main__":
    pytest.main([__file__]) 