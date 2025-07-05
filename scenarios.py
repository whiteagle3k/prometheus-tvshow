"""
TV Show Scenarios

Manages script injection and narrative scenarios for the reality show simulation.
Provides tools for creating, injecting, and managing storylines and character interactions.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


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
    """Manages scenarios and script injection for the TV show."""
    
    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}
        self.active_scenarios: List[str] = []
        self.scenario_history: List[Dict[str, Any]] = []
    
    def add_scenario(self, scenario: Scenario) -> None:
        """Add a new scenario to the manager."""
        self.scenarios[scenario.scenario_id] = scenario
        print(f"📝 Added scenario: {scenario.title}")
    
    def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """Get a scenario by ID."""
        return self.scenarios.get(scenario_id)
    
    def get_all_scenarios(self) -> List[Scenario]:
        """Get all scenarios."""
        return list(self.scenarios.values())
    
    def get_active_scenarios(self) -> List[Scenario]:
        """Get currently active scenarios."""
        return [self.scenarios[sid] for sid in self.active_scenarios if sid in self.scenarios]
    
    def activate_scenario(self, scenario_id: str) -> bool:
        """Activate a scenario."""
        if scenario_id in self.scenarios and scenario_id not in self.active_scenarios:
            self.active_scenarios.append(scenario_id)
            print(f"🎬 Activated scenario: {self.scenarios[scenario_id].title}")
            return True
        return False
    
    def deactivate_scenario(self, scenario_id: str) -> bool:
        """Deactivate a scenario."""
        if scenario_id in self.active_scenarios:
            self.active_scenarios.remove(scenario_id)
            print(f"⏸️ Deactivated scenario: {self.scenarios[scenario_id].title}")
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
    
    def get_scenario_history(self) -> List[Dict[str, Any]]:
        """Get execution history of scenarios."""
        return self.scenario_history.copy()


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
        ],
        priority=1
    )
    scenarios.append(intro_scenario)
    
    # Scenario 2: Creative challenge
    creative_scenario = Scenario(
        scenario_id="creative_challenge",
        title="Creative Challenge",
        description="Characters collaborate on a creative project",
        triggers=["create", "art", "project", "challenge"],
        characters=["leo", "emma"],
        script=[
            {
                "character": "leo",
                "action": "propose",
                "message": "Emma, I have an idea! What if we created something beautiful together? We could combine your innovation with my aesthetic sense!",
                "delay": 0
            },
            {
                "character": "emma",
                "action": "respond",
                "message": "Leo, that's brilliant! I have this crazy idea for a digital art installation that's never been done before. Want to hear it?",
                "delay": 2
            }
        ],
        priority=2
    )
    scenarios.append(creative_scenario)
    
    return scenarios 