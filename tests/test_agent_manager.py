"""
Test AgentManager and ChatContextBuilder integration with ExoLink.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from extensions.tvshow.agent_manager import AgentManager
from extensions.tvshow.context_builder import ChatContextBuilder


class TestAgentManager:
    """Test AgentManager ExoLink integration."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_registry = {
            "max": Mock(),
            "leo": Mock(),
            "emma": Mock()
        }
        self.agent_manager = AgentManager(self.mock_registry)
    
    @pytest.mark.asyncio
    async def test_route_message_to_agent_exolink_success(self):
        """Test successful message routing via ExoLink."""
        with patch('extensions.tvshow.agent_manager.router') as mock_router:
            mock_router.send.return_value = "Hello from ExoLink!"
            
            result = await self.agent_manager.route_message_to_agent(
                "max", "Hello Max!", context={"test": "context"}
            )
            
            # Verify ExoLink was called
            mock_router.send.assert_called_once()
            call_args = mock_router.send.call_args
            assert call_args[1]["content"] == "Hello Max!"
            assert call_args[1]["target"] == "entity:max"
            assert call_args[1]["source"] == "tvshow:user"
            
            # Verify result structure
            assert result["response"] == "Hello from ExoLink!"
            assert result["agent_id"] == "max"
            assert result["routed_via"] == "exolink"
            assert result["context"] == {"test": "context"}
    
    @pytest.mark.asyncio
    async def test_route_message_to_agent_exolink_fallback(self):
        """Test fallback to direct think() when ExoLink fails."""
        with patch('extensions.tvshow.agent_manager.router') as mock_router:
            mock_router.send.side_effect = Exception("ExoLink failed")
            
            # Mock the agent's think method
            mock_agent = AsyncMock()
            mock_agent.think.return_value = "Hello from direct think!"
            self.mock_registry["max"] = mock_agent
            
            result = await self.agent_manager.route_message_to_agent(
                "max", "Hello Max!"
            )
            
            # Verify fallback was used
            mock_agent.think.assert_called_once_with("Hello Max!")
            assert result["response"] == "Hello from direct think!"
            assert result["routed_via"] == "direct_fallback"
    
    @pytest.mark.asyncio
    async def test_route_message_to_agent_not_found(self):
        """Test error handling for non-existent agent."""
        with pytest.raises(ValueError, match="Agent unknown not found"):
            await self.agent_manager.route_message_to_agent("unknown", "Hello!")


class TestChatContextBuilder:
    """Test ChatContextBuilder functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_reflector = Mock()
        self.mock_scenario_manager = Mock()
        self.context_builder = ChatContextBuilder(
            self.mock_reflector, 
            self.mock_scenario_manager
        )
    
    def test_build_context_with_character(self):
        """Test context building for a specific character."""
        # Mock dependencies
        self.mock_reflector.get_scene_context_for_character.return_value = "Scene context"
        self.mock_scenario_manager.get_current_arc_context.return_value = "arc_id:test_arc phase_id:conflict"
        
        with patch('extensions.tvshow.context_builder.lore') as mock_lore:
            mock_lore.get_core_dream.return_value = "Core dream"
            mock_lore.get_traits.return_value = "Traits"
            mock_lore.get_law_of_emergence.return_value = "Law"
            
            context = self.context_builder.build_context("max", "Hello!")
            
            # Verify all components were called
            self.mock_reflector.get_scene_context_for_character.assert_called_once_with("max")
            self.mock_scenario_manager.get_current_arc_context.assert_called_once()
            mock_lore.get_core_dream.assert_called_once_with("max")
            mock_lore.get_traits.assert_called_once_with("max")
            mock_lore.get_law_of_emergence.assert_called_once()
            
            # Verify context structure
            assert context["scene_context"] == "Scene context"
            assert context["arc_context"] == "arc_id:test_arc phase_id:conflict"
            assert context["arc_id"] == "test_arc"
            assert context["phase_id"] == "conflict"
            assert context["core_dream"] == "Core dream"
            assert context["traits"] == "Traits"
            assert context["law"] == "Law"
            assert context["user_message"] == "Hello!"
    
    def test_build_context_without_character(self):
        """Test context building for scene messages (no character)."""
        # Mock dependencies
        self.mock_reflector.get_current_scene_summary.return_value = "Scene summary"
        self.mock_scenario_manager.get_current_arc_context.return_value = "arc_id:general phase_id:setup"
        
        with patch('extensions.tvshow.context_builder.lore') as mock_lore:
            mock_lore.get_law_of_emergence.return_value = "Law"
            
            context = self.context_builder.build_context(None, "Scene message")
            
            # Verify scene context was used instead of character context
            self.mock_reflector.get_current_scene_summary.assert_called_once()
            self.mock_reflector.get_scene_context_for_character.assert_not_called()
            
            # Verify no character-specific lore was called
            mock_lore.get_core_dream.assert_not_called()
            mock_lore.get_traits.assert_not_called()
            
            # Verify context structure
            assert context["scene_context"] == "Scene summary"
            assert context["arc_id"] == "general"
            assert context["phase_id"] == "setup"
            assert context["core_dream"] is None
            assert context["traits"] is None
            assert context["law"] == "Law"
            assert context["user_message"] == "Scene message"
    
    def test_extract_arc_phase(self):
        """Test arc and phase extraction from context."""
        # Test with both arc_id and phase_id
        arc_context = "arc_id:what_is_humanity phase_id:conflict"
        arc_id, phase_id = self.context_builder._extract_arc_phase(arc_context)
        assert arc_id == "what_is_humanity"
        assert phase_id == "conflict"
        
        # Test with only arc_id
        arc_context = "arc_id:test_arc"
        arc_id, phase_id = self.context_builder._extract_arc_phase(arc_context)
        assert arc_id == "test_arc"
        assert phase_id is None
        
        # Test with no arc information
        arc_context = "Just some context"
        arc_id, phase_id = self.context_builder._extract_arc_phase(arc_context)
        assert arc_id is None
        assert phase_id is None
        
        # Test with None
        arc_id, phase_id = self.context_builder._extract_arc_phase(None)
        assert arc_id is None
        assert phase_id is None 