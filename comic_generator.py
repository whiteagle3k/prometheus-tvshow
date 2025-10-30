from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional


class ComicGenerator:
    """Simple 4-panel ASCII comic generator.

    Panels are appended incrementally and exported to a timestamped file
    under the `episodes/` directory inside the tvshow extension by default.
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.panels: list[str] = []
        self.episode_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_dir = base_dir or (Path(__file__).parent / "episodes")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def add_panel(self, speaker: str, text: str, mood_emoji: str) -> None:
        speaker_label = speaker or "?"
        safe_text = (text or "").strip()
        emoji = (mood_emoji or "").strip()

        panel = (
            "   ┌──────┐\n"
            f"   │  {emoji}  │ {speaker_label}: \"{safe_text}\"\n"
            "   └──────┘"
        )
        self.panels.append(panel)

    def export(self, title: str = "AI House Episode") -> Path:
        header_bar = "═" * 50
        comic = (
            f"╔{header_bar}╗\n"
            f"║  {title}  ║\n"
            f"╚{header_bar}╝\n"
        )

        for index, panel in enumerate(self.panels[:4], start=1):
            comic += f"\n[COMIC PANEL {index}]\n{panel}\n"

        path = self.base_dir / f"episode_{self.episode_id}_comic.txt"
        with path.open("w", encoding="utf-8") as f:
            f.write(comic)

        print(f"[COMIC SAVED] {path}")
        return path


