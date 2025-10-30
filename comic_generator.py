from __future__ import annotations

import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class ComicGenerator:
    """ASCII and visual 4-panel comic generator.

    Supports fallback ASCII export and visual export via MCP xAI Image API.
    """

    def __init__(self, base_dir: Optional[Path] = None, use_visual: bool = False, mcp_url: str = "http://localhost:8080") -> None:
        self.panels: list[dict] = []
        self.episode_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_dir = base_dir or (Path(__file__).parent / "episodes")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.use_visual = use_visual
        self._mcp = None
        if self.use_visual:
            try:
                from mcp import MCPClient  # type: ignore
                self._mcp = MCPClient(base_url=mcp_url)
            except Exception:
                self._mcp = None
        self.character_prompts = self._load_character_prompts()

    def add_panel(self, speaker: str, text: str, mood_emoji: str) -> None:
        speaker_label = speaker or "?"
        safe_text = (text or "").strip()
        # Optional emoji mapping for known moods
        MOOD_EMOJI = {
            "sigh": "😔",
            "panic": "😱",
            "confident": "💪",
            "excited": "✨",
            "smirk": "😏",
            "default": "😐",
        }
        emoji_key = (mood_emoji or "").strip()
        emoji = MOOD_EMOJI.get(emoji_key, emoji_key or MOOD_EMOJI["default"])
        self.panels.append({
            "speaker": speaker_label,
            "text": safe_text,
            "mood": emoji_key or "default",
            "emoji": emoji,
        })

    async def export(self, title: str = "AI House Episode") -> Path:
        if self.use_visual and self._mcp is not None and len(self.panels) >= 4:
            try:
                return await self._export_visual(title)
            except Exception as exc:
                print(f"[VISUAL FAILED] {exc} → Falling back to ASCII")
                return self._export_ascii(title)
        return self._export_ascii(title)

    def _export_ascii(self, title: str) -> Path:
        header_bar = "═" * 50
        comic = (
            f"╔{header_bar}╗\n"
            f"║  {title}  ║\n"
            f"╚{header_bar}╝\n"
        )

        for index, panel in enumerate(self.panels[:4], start=1):
            ascii_panel = (
                "   ┌──────┐\n"
                f"   │  {panel['emoji']}  │ {panel['speaker']}: \"{panel['text']}\"\n"
                "   └──────┘"
            )
            comic += f"\n[COMIC PANEL {index}]\n{ascii_panel}\n"

        path = self.base_dir / f"episode_{self.episode_id}_comic.txt"
        with path.open("w", encoding="utf-8") as f:
            f.write(comic)

        print(f"[COMIC SAVED] {path}")
        return path

    async def _export_visual(self, title: str) -> Path:
        prompt = self._build_visual_prompt(title)
        result = await self._mcp.image_gen(
            prompt=prompt,
            width=1024,
            height=1024,
            num_images=1,
            seed=42,
        )
        img_b64 = result["images"][0] if isinstance(result, dict) else result.images[0]  # type: ignore
        img_data = base64.b64decode(img_b64)

        visual_dir = self.base_dir / "visual"
        visual_dir.mkdir(parents=True, exist_ok=True)
        png_path = visual_dir / f"episode_{self.episode_id}_comic.png"
        html_path = visual_dir / f"episode_{self.episode_id}_comic.html"
        with open(png_path, "wb") as f:
            f.write(img_data)
        self._generate_html_viewer(png_path, html_path, title)
        print(f"[VISUAL COMIC] {png_path}")
        return png_path

    def _build_visual_prompt(self, title: str) -> str:
        panels_desc: list[str] = []
        for i, p in enumerate(self.panels[:4]):
            char_desc = self.character_prompts.get(p["speaker"], "")
            mood_desc = f"{p['mood']} expression" if p['mood'] != 'default' else ""
            text = p['text'][:100]
            panels_desc.append(
                f"Panel {i+1}: {char_desc}, {mood_desc}, speech bubble: '{text}', in cluttered dorm room"
            )
        return (
            f"4-panel Pixar-style comic strip titled '{title}'. "
            f"Consistent character appearance across all panels. "
            f"Setting: cramped student dorm with kitchen, desk, bunk beds. "
            f"Panels: {'. '.join(panels_desc)}. "
            f"High detail, vibrant colors, emotional expressions."
        )

    def _generate_html_viewer(self, png_path: Path, html_path: Path, title: str) -> None:
        html = (
            "<!DOCTYPE html>\n"
            f"<html><head><title>{title}</title></head>\n"
            "<body style=\"text-align:center;background:#f0f0f0;\">\n"
            f"<h1>{title}</h1>\n"
            f"<img src=\"{png_path.name}\" style=\"max-width:100%;border:2px solid #333;\">\n"
            f"<p>Generated by AI House • {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>\n"
            "</body></html>\n"
        )
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

    def _load_character_prompts(self) -> dict[str, str]:
        return {
            "Max": "tall male with short brown hair, blue eyes, confident smile, red hoodie, Pixar 3D style",
            "Leo": "creative male with long black hair, paint-stained shirt, artistic pose, Pixar 3D style",
            "Emma": "female with glasses, blonde ponytail, anxious expression, blue sweater, Pixar 3D style",
            "Marvin": "Marvin the Paranoid Android: tall gray robot, oversized head, sad green LED eyes, hunched posture, carrying tiny 'Don't Panic' towel, Pixar 3D style",
        }


