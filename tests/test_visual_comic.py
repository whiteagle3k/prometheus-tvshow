import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from extensions.tvshow.comic_generator import ComicGenerator

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


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


@pytest.mark.skipif(not PIL_AVAILABLE, reason="Pillow not available")
def test_overlay_applies(tmp_path):
    """Test that text overlay applies correctly to speech bubbles."""
    from PIL import Image
    
    comic = ComicGenerator(base_dir=tmp_path)
    comic.panels = [
        {"speaker": "Emma", "text": "My code crashed!", "mood": "panic", "emoji": "😱"},
        {"speaker": "Max", "text": "We can fix this!", "mood": "confident", "emoji": "💪"},
        {"speaker": "Marvin", "text": "Why bother?", "mood": "sigh", "emoji": "😔"},
        {"speaker": "Leo", "text": "His pain fuels my art!", "mood": "excited", "emoji": "✨"},
    ]
    
    # Create a test image
    img = Image.new("RGB", (1024, 1024), "lightgray")
    
    # Apply overlay
    result = comic._add_speech_bubbles(img, comic.panels[:4])
    
    # Verify result
    assert result.size == (1024, 1024)
    assert result is not img  # Should be a new image


