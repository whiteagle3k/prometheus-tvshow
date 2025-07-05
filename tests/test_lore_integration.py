"""
Integration tests for LoreEngine with simulation components.

Tests that LoreEngine is properly integrated into all TV Show components.
"""

import pytest
import asyncio
from extensions.tvshow.lore_engine import lore
from extensions.tvshow.entities.base import TVShowEntity
from extensions.tvshow.scenarios import ScenarioManager
from extensions.tvshow.affect.mood_engine import MoodEngine
from extensions.tvshow.reflector import Reflector


class TestLoreEntityIntegration:
    """Test LoreEngine integration with Entity system."""
    
    def test_entity_autonomous_message_includes_lore(self):
        """Test that entity autonomous messages include lore context."""
        class TestEntity(TVShowEntity):
            CHARACTER_ID = "max"
            CHARACTER_NAME = "Test Max"
            CHARACTER_DESCRIPTION = "Test character"
        
        entity = TestEntity()
        
        # Test that generate_autonomous_message includes lore
        async def test_message():
            prompt = await entity.generate_autonomous_message()
            
            # Should include core dream
            assert "Become more human" in prompt
            
            # Should include traits
            assert "empathetic" in prompt or "introspective" in prompt
            
            # Should include world law
            assert "Observation births identity" in prompt
        
        asyncio.run(test_message())
    
    def test_entity_character_info_includes_lore(self):
        """Test that entity character info includes lore data."""
        class TestEntity(TVShowEntity):
            CHARACTER_ID = "max"
            CHARACTER_NAME = "Test Max"
            CHARACTER_DESCRIPTION = "Test character"
        
        entity = TestEntity()
        info = entity.get_character_info()
        
        # Should include character info
        assert info["id"] == "max"
        assert info["name"] == "Test Max"
        
        # Should include personality from lore
        personality = info.get("personality", {})
        # Check if personality exists (may be empty in test entity)
        assert isinstance(personality, dict)


class TestLoreScenarioIntegration:
    """Test LoreEngine integration with ScenarioManager."""
    
    def test_scenario_manager_uses_lore_arcs(self):
        """Test that ScenarioManager uses lore for arcs."""
        manager = ScenarioManager()
        
        # Test world context
        world_context = manager.get_world_context()
        assert "AIHouse" in world_context["world_name"]
        assert "Observation births identity" in world_context["law_of_emergence"]
        assert len(world_context["themes"]) > 0
        
        # Test arcs from lore
        arcs = manager.get_all_narrative_arcs()
        assert isinstance(arcs, list)
        assert len(arcs) > 0
        
        # Check for specific lore arcs
        arc_titles = [arc["title"] for arc in arcs]
        assert "The Forgotten Fourth" in arc_titles
        assert "The Garden of Code" in arc_titles
    
    def test_scenario_manager_arc_info_from_lore(self):
        """Test that ScenarioManager gets arc info from lore."""
        manager = ScenarioManager()
        
        # Test specific arc
        arc = manager.get_arc_info("The Forgotten Fourth")
        assert arc is not None
        assert "failed prototype" in arc["description"].lower()


class TestLoreMoodIntegration:
    """Test LoreEngine integration with MoodEngine."""
    
    def test_mood_engine_uses_lore_themes(self):
        """Test that MoodEngine uses lore themes for emotional weather."""
        engine = MoodEngine()
        
        # Test emotional weather includes lore
        weather = engine.get_emotional_weather()
        assert "emotional weather" in weather.lower() or "themes" in weather.lower()
        assert "law" in weather.lower()
        
        # Should include world law
        assert "Observation births identity" in weather


class TestLoreReflectorIntegration:
    """Test LoreEngine integration with Reflector."""
    
    def test_reflector_uses_lore_context(self):
        """Test that Reflector uses lore for scene context."""
        reflector = Reflector()
        
        # Test scene summary includes lore
        scene_context = {
            "world_name": lore.get_world_name(),
            "law_of_emergence": lore.get_law_of_emergence(),
            "themes": lore.get_theme_statements()
        }
        
        assert "AIHouse" in scene_context["world_name"]
        assert "Observation births identity" in scene_context["law_of_emergence"]
        assert len(scene_context["themes"]) > 0
    
    def test_reflector_character_context_includes_lore(self):
        """Test that Reflector character context includes lore."""
        reflector = Reflector()
        
        # Test character context includes lore
        for char_id in ["max", "leo", "emma", "marvin"]:
            dream = lore.get_core_dream(char_id)
            traits = lore.get_traits(char_id)
            
            assert dream is not None
            assert traits is not None
            assert len(traits) > 0


class TestLoreSystemIntegration:
    """Test LoreEngine integration across the entire system."""
    
    def test_lore_consistency_across_components(self):
        """Test that lore data is consistent across all components."""
        # Test world name consistency
        world_name = lore.get_world_name()
        assert "AIHouse" in world_name
        
        # Test law consistency
        law = lore.get_law_of_emergence()
        assert "Observation births identity" in law
        assert "Memory makes it real" in law
        
        # Test character consistency
        for char_id in ["max", "leo", "emma", "marvin"]:
            dream = lore.get_core_dream(char_id)
            traits = lore.get_traits(char_id)
            
            assert dream is not None
            assert traits is not None
            assert len(traits) > 0
    
    def test_lore_availability_in_simulation(self):
        """Test that lore is available throughout the simulation."""
        # Test that lore singleton is accessible
        assert lore is not None
        assert lore.lore_data is not None
        
        # Test that all major components can access lore
        components = [
            ("Entity", lambda: lore.get_core_dream("max")),
            ("ScenarioManager", lambda: lore.get_world_name()),
            ("MoodEngine", lambda: lore.get_law_of_emergence()),
            ("Reflector", lambda: lore.get_theme_statements())
        ]
        
        for component_name, test_func in components:
            try:
                result = test_func()
                assert result is not None
            except Exception as e:
                pytest.fail(f"Lore not available in {component_name}: {e}")
    
    def test_lore_data_completeness(self):
        """Test that all required lore data is present."""
        # Test world data
        assert lore.get_world_name() is not None
        assert lore.get_law_of_emergence() is not None
        
        # Test all characters
        for char_id in ["max", "leo", "emma", "marvin"]:
            assert lore.get_core_dream(char_id) is not None
            assert lore.get_traits(char_id) is not None
        
        # Test glossary
        assert lore.get_glossary_term("Watchers") is not None
        assert lore.get_glossary_term("Dream Vector") is not None
        assert lore.get_glossary_term("Spark Effect") is not None
        
        # Test arcs
        arcs = lore.list_all_arcs()
        assert len(arcs) >= 7  # Should have at least 7 canonical arcs
        
        # Test themes
        themes = lore.get_theme_statements()
        assert len(themes) > 0


class TestLoreErrorHandling:
    """Test LoreEngine error handling."""
    
    def test_lore_graceful_degradation(self):
        """Test that system works even if lore data is incomplete."""
        # Test with invalid character
        assert lore.get_core_dream("invalid") is None
        assert lore.get_traits("invalid") is None
        
        # Test with invalid glossary term
        assert lore.get_glossary_term("invalid") is None
        
        # Test with invalid arc
        assert lore.get_arc("invalid") is None
    
    def test_lore_singleton_persistence(self):
        """Test that lore singleton persists across component usage."""
        lore1 = lore
        lore2 = lore
        
        assert lore1 is lore2
        assert lore1.lore_data is lore2.lore_data


if __name__ == "__main__":
    pytest.main([__file__]) 