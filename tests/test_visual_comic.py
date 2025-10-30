import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from extensions.tvshow.comic_generator import ComicGenerator


@pytest.mark.asyncio
async def test_visual_export_fallback(monkeypatch, tmp_path):
    comic = ComicGenerator(base_dir=tmp_path, use_visual=True)
    comic.panels = [
        {"speaker": "Marvin", "text": "Why bother?", "mood": "sigh", "emoji": "😔"}
    ] * 4

    # If MCP client was not created, emulate it to test fallback path
    class DummyMCP:
        async def image_gen(self, **kwargs):
            raise Exception("API down")

    if comic._mcp is None:
        comic._mcp = DummyMCP()
    else:
        monkeypatch.setattr(comic._mcp, "image_gen", AsyncMock(side_effect=Exception("API down")))

    path = await comic.export("Test Visual Fallback")
    # Should fall back to ASCII and create a .txt file
    assert path.suffix == ".txt"
    assert path.exists()


