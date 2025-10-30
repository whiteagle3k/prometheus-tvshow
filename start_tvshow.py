#!/usr/bin/env python3
"""
TV Show Extension Startup Script

Starts the TV show backend server with UI support.
"""

import uvicorn
import asyncio
import sys
import os
import argparse

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from extensions.tvshow.voice_narrator import VoiceNarrator
from extensions.tvshow.comic_generator import ComicGenerator

async def init_system():
    """Initialize the Prometheus system with TV show characters."""
    print("🎭 Initializing Prometheus system with TV show characters...")
    # Lazy import to avoid heavy deps during demo tests
    from core.runtime.lifecycle import startup_system  # type: ignore
    
    # Get all character IDs
    from extensions.tvshow.entities import get_all_characters
    character_ids = list(get_all_characters().keys())
    
    # Initialize the system with all characters
    success = await startup_system(character_ids)
    if success:
        print(f"✅ System initialized with characters: {', '.join(character_ids)}")
    else:
        print("❌ Failed to initialize system")
    
    return success

async def _run_demo(voice_enabled: bool, comics_enabled: bool) -> None:
    """Run a short, scripted demo episode.

    This does not require the full backend to be running and is safe for CI.
    """
    voice = VoiceNarrator() if voice_enabled else None
    comic = ComicGenerator() if comics_enabled else None

    lines = [
        ("Narrator", "Emma's code just crashed. Deadline in 2 hours.", "panic"),
        ("Emma", "I... I failed everyone.", "sad"),
        ("Max", "We fix this TOGETHER. Leo, sketch ideas?", "confident"),
        ("Leo", "Inspired! Let me draw!", "excited"),
        ("Marvin", "Heh, classic overthink.", "smirk"),
    ]

    mood_to_emoji = {
        "panic": "😱",
        "sad": "😢",
        "confident": "💪",
        "excited": "✨",
        "smirk": "😏",
    }

    for speaker, text, mood in lines:
        print(f"[{speaker}] {text}")
        if voice is not None:
            await voice.speak(text)
        if comic is not None:
            emoji = mood_to_emoji.get(mood, "😐")
            comic.add_panel(speaker, text, emoji)
        await asyncio.sleep(0.1)

    if comic is not None:
        comic.export("Demo: Project Crisis")


def main():
    """Start the TV show server, or run demo mode if requested."""
    parser = argparse.ArgumentParser(description="TVShow Extension Launcher")
    parser.add_argument("--demo", action="store_true", help="Run auto demo and exit")
    parser.add_argument("--voice", action="store_true", help="Enable voice narration in demo mode")
    parser.add_argument("--comics", action="store_true", help="Export ASCII comics in demo mode")
    args = parser.parse_args()

    if args.demo:
        print("🎬 Running TV Show Demo Mode...")
        asyncio.run(_run_demo(voice_enabled=args.voice, comics_enabled=args.comics))
        return

    print("🎬 Starting TV Show Extension...")
    print("=" * 50)
    print("📺 TV Show Director Console")
    print("🌐 Backend API: http://localhost:8000")
    print("🎭 UI Console: http://localhost:8000/tvshow")
    print("📋 API Docs: http://localhost:8000/docs")
    print("=" * 50)

    # Initialize the system
    asyncio.run(init_system())

    # Create router and get app (lazy import to keep demo/CI lightweight)
    from extensions.tvshow.router import TVShowRouter
    router = TVShowRouter()
    app = router.get_app()

    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )

if __name__ == "__main__":
    main() 