from extensions.tvshow.lore_engine import lore

class MoodEngine:
    def get_emotional_weather(self) -> str:
        # Use lore for emotional weather description
        themes = lore.get_theme_statements()
        law = lore.get_law_of_emergence()
        return f"Emotional weather is shaped by: {', '.join(themes)}. World law: {law}" 