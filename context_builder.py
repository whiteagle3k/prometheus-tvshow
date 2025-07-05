# extensions/tvshow/context_builder.py
from extensions.tvshow.lore_engine import lore

class ChatContextBuilder:
    def __init__(self, reflector, scenario_manager):
        self.reflector = reflector
        self.scenario_manager = scenario_manager

    def build_context(self, character_id: str, user_message: str) -> dict:
        scene_context = self.reflector.get_scene_context_for_character(character_id) if character_id else self.reflector.get_current_scene_summary()
        arc_context = self.scenario_manager.get_current_arc_context()
        arc_id, phase_id = self._extract_arc_phase(arc_context)
        core_dream = lore.get_core_dream(character_id) if character_id else None
        traits = lore.get_traits(character_id) if character_id else None
        law = lore.get_law_of_emergence()
        return {
            "scene_context": scene_context,
            "arc_context": arc_context,
            "arc_id": arc_id,
            "phase_id": phase_id,
            "core_dream": core_dream,
            "traits": traits,
            "law": law,
            "user_message": user_message
        }

    def _extract_arc_phase(self, arc_context: str):
        # Dummy extraction; replace with real parsing if needed
        arc_id = None
        phase_id = None
        if arc_context and isinstance(arc_context, str):
            if "arc_id:" in arc_context:
                arc_id = arc_context.split("arc_id:")[1].split()[0]
            if "phase_id:" in arc_context:
                phase_id = arc_context.split("phase_id:")[1].split()[0]
        return arc_id, phase_id 