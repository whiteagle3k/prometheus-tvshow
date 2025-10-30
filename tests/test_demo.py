import asyncio
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path for "extensions" imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from extensions.tvshow.comic_generator import ComicGenerator


def test_comic_generator_exports_four_panels(tmp_path: Path) -> None:
    generator = ComicGenerator(base_dir=tmp_path)
    # Add more than 4 to ensure truncation to 4 panels in export
    for i in range(6):
        generator.add_panel("Max", f"Line {i}", "✨")
    out_path = generator.export("Unit Test Episode")
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    # Expect exactly 4 panel headings
    assert content.count("[COMIC PANEL ") == 4


def test_demo_episode_creates_comic(tmp_path: Path, monkeypatch) -> None:
    # Import here to avoid importing uvicorn app lifecycle during collection
    from extensions.tvshow.start_tvshow import _run_demo

    # Redirect episodes output to tmp_path by monkeypatching ComicGenerator base_dir
    from extensions.tvshow import comic_generator as cg_module

    original_init = cg_module.ComicGenerator.__init__

    def _patched_init(self, base_dir=None):  # type: ignore
        original_init(self, base_dir=tmp_path)

    monkeypatch.setattr(cg_module.ComicGenerator, "__init__", _patched_init)

    before = set(tmp_path.glob("*.txt"))
    asyncio.run(_run_demo(voice_enabled=False, comics_enabled=True))
    after = set(tmp_path.glob("*.txt"))
    created = list(after - before)
    assert len(created) == 1
    assert created[0].read_text(encoding="utf-8").startswith("╔")


