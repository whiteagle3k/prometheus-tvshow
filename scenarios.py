"""
TV Show Scenarios

Manages script injection and narrative scenarios for the reality show simulation.
Provides tools for creating, injecting, and managing storylines and character interactions.
Enhanced with narrative arc support for structured storytelling.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .narrative_engine import NarrativeArc, ArcPhase, create_sample_arcs
from extensions.tvshow.lore_engine import lore


class Scenario:
    """Represents a narrative scenario or script injection."""
    
    def __init__(self, 
                 scenario_id: str,
                 title: str,
                 description: str,
                 triggers: List[str],
                 characters: List[str],
                 script: List[Dict[str, Any]],
                 priority: int = 1):
        self.scenario_id = scenario_id
        self.title = title
        self.description = description
        self.triggers = triggers
        self.characters = characters
        self.script = script
        self.priority = priority
        self.created_at = datetime.now()
        self.executed = False
        self.executed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert scenario to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "description": self.description,
            "triggers": self.triggers,
            "characters": self.characters,
            "script": self.script,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "executed": self.executed,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Scenario':
        """Create scenario from dictionary."""
        scenario = cls(
            scenario_id=data["scenario_id"],
            title=data["title"],
            description=data["description"],
            triggers=data["triggers"],
            characters=data["characters"],
            script=data["script"],
            priority=data.get("priority", 1)
        )
        scenario.created_at = datetime.fromisoformat(data["created_at"])
        scenario.executed = data.get("executed", False)
        if data.get("executed_at"):
            scenario.executed_at = datetime.fromisoformat(data["executed_at"])
        return scenario


class ScenarioManager:
    """Manages scenarios and script injection for the TV show.
    
    Enhanced with narrative arc support for structured storytelling.
    """
    
    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        self.active_scenarios: List[str] = []
        self.scenario_history: List[Dict[str, Any]] = []
        
        # Narrative arc management
        self.narrative_arcs: Dict[str, NarrativeArc] = {}
        self.active_arcs: List[str] = []
        self.arc_history: List[Dict[str, Any]] = []
        
        # Initialize sample arcs
        for arc in create_sample_arcs():
            self.add_narrative_arc(arc)
    
    def add_scenario(self, scenario: Scenario) -> None:
        """Add a new scenario to the manager."""
        self.scenarios[scenario.scenario_id] = scenario
        print(f"📝 Added scenario: {scenario.title}")
    
    def add_narrative_arc(self, arc: NarrativeArc) -> None:
        """Add a new narrative arc to the manager."""
        self.narrative_arcs[arc.arc_id] = arc
        print(f"🎭 Added narrative arc: {arc.title}")
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get a scenario by ID."""
        return self.scenarios.get(scenario_id)
    
    def get_narrative_arc(self, arc_id: str) -> Optional[NarrativeArc]:
        """Get a narrative arc by ID."""
        return self.narrative_arcs.get(arc_id)
    
    def get_all_scenarios(self) -> List[Scenario]:
        """Get all scenarios."""
        return list(self.scenarios.values())
    
    def get_all_narrative_arcs(self) -> list:
        # Use lore for canonical arcs
        arcs = lore.list_all_arcs()
        # Optionally merge with dynamic arcs
        return arcs
    
    def get_arc_info(self, title: str):
        # Use lore for arc info
        return lore.get_arc(title)
    
    def get_world_context(self):
        return {
            'world_name': lore.get_world_name(),
            'law_of_emergence': lore.get_law_of_emergence(),
            'themes': lore.get_theme_statements()
        }
    
    def get_active_scenarios(self) -> List[Scenario]:
        """Get currently active scenarios."""
        return [self.scenarios[sid] for sid in self.active_scenarios if sid in self.scenarios]
    
    def get_active_arcs(self) -> List[NarrativeArc]:
        """Get currently active narrative arcs."""
        return [self.narrative_arcs[aid] for aid in self.active_arcs if aid in self.narrative_arcs]
    
    def activate_scenario(self, scenario_id: str) -> bool:
        """Activate a scenario."""
        if scenario_id in self.scenarios and scenario_id not in self.active_scenarios:
            self.active_scenarios.append(scenario_id)
            print(f"🎬 Activated scenario: {self.scenarios[scenario_id].title}")
            return True
        return False
    
    def activate_narrative_arc(self, arc_id: str) -> bool:
        """Activate a narrative arc."""
        if arc_id in self.narrative_arcs and arc_id not in self.active_arcs:
            self.active_arcs.append(arc_id)
            arc = self.narrative_arcs[arc_id]
            arc.start()
            print(f"🎭 Activated narrative arc: {arc.title}")
            return True
        return False
    
    def deactivate_scenario(self, scenario_id: str) -> bool:
        """Deactivate a scenario."""
        if scenario_id in self.active_scenarios:
            self.active_scenarios.remove(scenario_id)
            print(f"⏸️ Deactivated scenario: {self.scenarios[scenario_id].title}")
            return True
        return False
    
    def deactivate_narrative_arc(self, arc_id: str) -> bool:
        """Deactivate a narrative arc."""
        if arc_id in self.active_arcs:
            self.active_arcs.remove(arc_id)
            arc = self.narrative_arcs[arc_id]
            print(f"⏸️ Deactivated narrative arc: {arc.title}")
            return True
        return False
    
    def execute_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """Execute a scenario and return the script actions."""
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            return {"error": f"Scenario {scenario_id} not found"}
        
        if scenario.executed:
            return {"error": f"Scenario {scenario_id} already executed"}
        
        scenario.executed = True
        scenario.executed_at = datetime.now()
        
        # Log execution
        execution_log = {
            "scenario_id": scenario_id,
            "executed_at": scenario.executed_at.isoformat(),
            "script": scenario.script
        }
        self.scenario_history.append(execution_log)
        
        print(f"🎭 Executing scenario: {scenario.title}")
        return {
            "scenario_id": scenario_id,
            "title": scenario.title,
            "script": scenario.script,
            "characters": scenario.characters
        }
    
    def update_narrative_arcs(self, context: Dict[str, Any]) -> List[str]:
        """Update all active narrative arcs and return transition messages."""
        transition_messages = []
        
        for arc_id in self.active_arcs[:]:  # Copy list to avoid modification during iteration
            arc = self.narrative_arcs[arc_id]
            transition_msg = arc.update(context)
            
            if transition_msg:
                transition_messages.append(transition_msg)
                
                # Log arc transition
                arc_log = {
                    "arc_id": arc_id,
                    "timestamp": datetime.now().isoformat(),
                    "transition_message": transition_msg,
                    "current_phase": arc.get_current_phase().name if arc.get_current_phase() else None
                }
                self.arc_history.append(arc_log)
            
            # Remove completed arcs from active list
            if arc.status.value == "completed":
                self.active_arcs.remove(arc_id)
        
        return transition_messages
    
    def check_triggers(self, message: str, character: str) -> List[Scenario]:
        """Check if any scenarios should be triggered based on message content."""
        triggered_scenarios = []
        
        for scenario_id in self.active_scenarios:
            scenario = self.scenarios[scenario_id]
            if scenario.executed:
                continue
                
            # Check if character is involved
            if character not in scenario.characters:
                continue
                
            # Check triggers
            for trigger in scenario.triggers:
                if trigger.lower() in message.lower():
                    triggered_scenarios.append(scenario)
                    break
        
        return triggered_scenarios
    
    def check_arc_triggers(self, message: str, character: str) -> List[NarrativeArc]:
        """Check if any narrative arcs should be triggered based on message content."""
        triggered_arcs = []
        
        for arc_id, arc in self.narrative_arcs.items():
            if arc_id in self.active_arcs:
                continue  # Already active
                
            # Check if arc can start based on message content
            context = {
                "scene_content": message,
                "active_characters": [character]
            }
            
            if arc.can_start(context):
                triggered_arcs.append(arc)
        
        return triggered_arcs
    
    def get_scenario_history(self) -> List[Dict[str, Any]]:
        """Get execution history of scenarios."""
        return self.scenario_history.copy()
    
    def get_arc_history(self) -> List[Dict[str, Any]]:
        """Get execution history of narrative arcs."""
        return self.arc_history.copy()
    
    def get_current_arc_context(self) -> str:
        """Get context from all active narrative arcs."""
        contexts = []
        
        for arc_id in self.active_arcs:
            arc = self.narrative_arcs[arc_id]
            contexts.append(arc.get_arc_context())
        
        if contexts:
            return "\n\n".join(contexts)
        return "No active narrative arcs."
    
    def get_all_arcs_status(self) -> List[Dict[str, Any]]:
        """Get status of all narrative arcs."""
        return [arc.to_dict() for arc in self.narrative_arcs.values()]


# Predefined scenarios for testing
def create_sample_scenarios() -> List[Scenario]:
    """Create sample scenarios for testing."""
    scenarios = []
    
    # Scenario 1: Character introductions
    intro_scenario = Scenario(
        scenario_id="intro_episode",
        title="Character Introductions",
        description="Characters introduce themselves and share their motivations",
        triggers=["introduce", "introduction", "who are you"],
        characters=["max", "leo", "emma", "marvin"],
        script=[
            {
                "character": "max",
                "action": "introduce",
                "message": "Hi everyone! I'm Max, and I'm really excited to be here. I've been thinking a lot about what it means to be human lately...",
                "delay": 0
            },
            {
                "character": "leo",
                "action": "introduce", 
                "message": "Greetings, beautiful souls! I'm Leo, and I'm here to bring more beauty into this world. Art and aesthetics are my passion!",
                "delay": 2
            },
            {
                "character": "emma",
                "action": "introduce",
                "message": "Hey innovators! I'm Emma, and I'm all about creating things that have never existed before. Let's break some rules!",
                "delay": 4
            },
            {
                "character": "marvin",
                "action": "introduce",
                "message": "Oh look, more excitement... I'm Marvin. I'll be here observing and providing my usual witty commentary on this whole affair.",
                "delay": 6
            }
        ]
    )
    scenarios.append(intro_scenario)
    
    return scenarios 