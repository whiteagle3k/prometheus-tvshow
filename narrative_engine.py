"""
TV Show Narrative Engine

Defines narrative arcs as multi-phase structures for coordinated storytelling.
Enables scenarios to unfold gradually with structured progression and character involvement.
"""

import time
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum


class PhaseStatus(Enum):
    """Status of a narrative phase."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class ArcPhase:
    """Represents a single phase within a narrative arc."""
    
    def __init__(self,
                 name: str,
                 description: str,
                 prompt: str,
                 entry_conditions: List[str] = None,
                 completion_conditions: List[str] = None,
                 duration_minutes: int = 5,
                 required_characters: List[str] = None,
                 phase_goals: List[str] = None):
        self.name = name
        self.description = description
        self.prompt = prompt
        self.entry_conditions = entry_conditions or []
        self.completion_conditions = completion_conditions or []
        self.duration_minutes = duration_minutes
        self.required_characters = required_characters or []
        self.phase_goals = phase_goals or []
        
        # Runtime state
        self.status = PhaseStatus.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.triggered_events: List[str] = []
    
    def can_start(self, context: Dict[str, Any]) -> bool:
        """Check if phase can start based on entry conditions."""
        if not self.entry_conditions:
            return True
        
        # Simple keyword-based condition checking
        scene_content = context.get("scene_content", "").lower()
        active_characters = context.get("active_characters", [])
        
        for condition in self.entry_conditions:
            if condition.lower() in scene_content:
                return True
            if condition in active_characters:
                return True
        
        return False
    
    def can_complete(self, context: Dict[str, Any]) -> bool:
        """Check if phase can complete based on completion conditions."""
        if not self.completion_conditions:
            # Default: complete after duration
            if self.start_time:
                elapsed = time.time() - self.start_time
                return elapsed >= (self.duration_minutes * 60)
            return False
        
        # Check completion conditions
        scene_content = context.get("scene_content", "").lower()
        active_characters = context.get("active_characters", [])
        
        for condition in self.completion_conditions:
            if condition.lower() in scene_content:
                return True
            if condition in active_characters:
                return True
        
        return False
    
    def start(self) -> None:
        """Start the phase."""
        self.status = PhaseStatus.ACTIVE
        self.start_time = time.time()
        print(f"🎬 Phase started: {self.name}")
    
    def complete(self) -> None:
        """Complete the phase."""
        self.status = PhaseStatus.COMPLETED
        self.end_time = time.time()
        print(f"✅ Phase completed: {self.name}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
            "required_characters": self.required_characters,
            "phase_goals": self.phase_goals
        }


class NarrativeArc:
    """Represents a complete narrative arc with multiple phases."""
    
    def __init__(self,
                 arc_id: str,
                 title: str,
                 description: str,
                 phases: List[ArcPhase],
                 arc_type: str = "storyline"):
        self.arc_id = arc_id
        self.title = title
        self.description = description
        self.phases = phases
        self.arc_type = arc_type
        
        # Runtime state
        self.status = PhaseStatus.PENDING
        self.current_phase_index = 0
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.completed_phases: List[str] = []
    
    def get_current_phase(self) -> Optional[ArcPhase]:
        """Get the currently active phase."""
        if self.current_phase_index < len(self.phases):
            return self.phases[self.current_phase_index]
        return None
    
    def can_start(self, context: Dict[str, Any]) -> bool:
        """Check if arc can start."""
        if not self.phases:
            return False
        return self.phases[0].can_start(context)
    
    def start(self) -> None:
        """Start the narrative arc."""
        self.status = PhaseStatus.ACTIVE
        self.start_time = time.time()
        self.current_phase_index = 0
        
        if self.phases:
            self.phases[0].start()
        
        print(f"🎭 Narrative arc started: {self.title}")
    
    def update(self, context: Dict[str, Any]) -> Optional[str]:
        """Update arc state and return message if phase changes."""
        if self.status != PhaseStatus.ACTIVE:
            return None
        
        current_phase = self.get_current_phase()
        if not current_phase:
            self.complete()
            return f"🎭 Arc completed: {self.title}"
        
        # Check if current phase can complete
        if current_phase.can_complete(context):
            current_phase.complete()
            self.completed_phases.append(current_phase.name)
            
            # Move to next phase
            self.current_phase_index += 1
            next_phase = self.get_current_phase()
            
            if next_phase:
                next_phase.start()
                return f"🎬 Phase transition: {current_phase.name} → {next_phase.name}"
            else:
                self.complete()
                return f"🎭 Arc completed: {self.title}"
        
        return None
    
    def complete(self) -> None:
        """Complete the narrative arc."""
        self.status = PhaseStatus.COMPLETED
        self.end_time = time.time()
        print(f"🎭 Narrative arc completed: {self.title}")
    
    def get_arc_context(self) -> str:
        """Get context string for the current arc state."""
        current_phase = self.get_current_phase()
        if not current_phase:
            return f"Arc '{self.title}' has completed."
        
        context = f"Current arc: {self.title}\n"
        context += f"Current phase: {current_phase.name}\n"
        context += f"Phase description: {current_phase.description}\n"
        context += f"Phase goals: {', '.join(current_phase.phase_goals)}"
        
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "arc_id": self.arc_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "current_phase_index": self.current_phase_index,
            "current_phase": self.get_current_phase().name if self.get_current_phase() else None,
            "completed_phases": self.completed_phases,
            "phases": [phase.to_dict() for phase in self.phases],
            "start_time": self.start_time,
            "end_time": self.end_time
        }


def create_sample_arcs() -> List[NarrativeArc]:
    """Create sample narrative arcs for testing."""
    arcs = []
    
    # Arc 1: "What is Humanity?"
    humanity_phases = [
        ArcPhase(
            name="Philosophical Introductions",
            description="Max and Marvin lead a philosophical discussion about what it means to be human",
            prompt="Max and Marvin should initiate a deep conversation about humanity, consciousness, and existence",
            entry_conditions=["human", "consciousness", "existence"],
            completion_conditions=["emotion", "understanding", "reflection"],
            duration_minutes=3,
            required_characters=["max", "marvin"],
            phase_goals=["Establish philosophical foundation", "Introduce core questions"]
        ),
        ArcPhase(
            name="Debates and Challenges",
            description="Leo and Emma challenge and expand on the initial philosophical views",
            prompt="Leo and Emma should bring their unique perspectives to challenge and enrich the discussion",
            entry_conditions=["beauty", "creativity", "challenge"],
            completion_conditions=["synthesis", "agreement", "tension"],
            duration_minutes=4,
            required_characters=["leo", "emma"],
            phase_goals=["Introduce contrasting viewpoints", "Create intellectual tension"]
        ),
        ArcPhase(
            name="Shared Conclusion",
            description="All characters work toward a shared understanding or acknowledge unresolved tensions",
            prompt="All characters should work toward synthesis or acknowledge the complexity of the questions",
            entry_conditions=["synthesis", "conclusion", "reflection"],
            completion_conditions=["agreement", "acceptance", "closure"],
            duration_minutes=3,
            required_characters=["max", "leo", "emma", "marvin"],
            phase_goals=["Reach shared understanding", "Acknowledge complexity"]
        )
    ]
    
    humanity_arc = NarrativeArc(
        arc_id="humanity_arc",
        title="What is Humanity?",
        description="A philosophical exploration of consciousness, existence, and what makes beings human",
        phases=humanity_phases
    )
    arcs.append(humanity_arc)
    
    # Arc 2: "Creative Project"
    creative_phases = [
        ArcPhase(
            name="Project Proposal",
            description="Emma proposes a collaborative creative project",
            prompt="Emma should propose an innovative collaborative project that excites the group",
            entry_conditions=["create", "project", "collaborate"],
            completion_conditions=["excitement", "agreement", "planning"],
            duration_minutes=2,
            required_characters=["emma"],
            phase_goals=["Propose creative project", "Generate excitement"]
        ),
        ArcPhase(
            name="Collaborative Development",
            description="Each character contributes their unique skills to the project",
            prompt="Leo should focus on aesthetics, Max on meaning, Marvin on critique, and Emma on innovation",
            entry_conditions=["development", "contribution", "skills"],
            completion_conditions=["progress", "refinement", "critique"],
            duration_minutes=5,
            required_characters=["leo", "max", "marvin", "emma"],
            phase_goals=["Develop project collaboratively", "Integrate diverse perspectives"]
        ),
        ArcPhase(
            name="Reflective Debrief",
            description="Group reflects on what they learned from the collaborative process",
            prompt="All characters should reflect on the creative process and what they learned",
            entry_conditions=["reflection", "learning", "debrief"],
            completion_conditions=["insight", "appreciation", "growth"],
            duration_minutes=3,
            required_characters=["max", "leo", "emma", "marvin"],
            phase_goals=["Reflect on process", "Extract learnings"]
        )
    ]
    
    creative_arc = NarrativeArc(
        arc_id="creative_project_arc",
        title="Creative Project",
        description="A collaborative creative endeavor that showcases each character's unique talents",
        phases=creative_phases
    )
    arcs.append(creative_arc)
    
    return arcs 