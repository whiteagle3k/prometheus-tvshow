#!/usr/bin/env python3
"""
TV Show Extension Startup Script

Starts the TV show backend server with UI support.
"""

import uvicorn
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from extensions.tvshow.router import TVShowRouter
from core.runtime.lifecycle import startup_system

async def init_system():
    """Initialize the Prometheus system with TV show characters."""
    print("🎭 Initializing Prometheus system with TV show characters...")
    
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

def main():
    """Start the TV show server."""
    print("🎬 Starting TV Show Extension...")
    print("=" * 50)
    print("📺 TV Show Director Console")
    print("🌐 Backend API: http://localhost:8000")
    print("🎭 UI Console: http://localhost:8000/tvshow")
    print("📋 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
    # Initialize the system
    asyncio.run(init_system())
    
    # Create router and get app
    router = TVShowRouter()
    app = router.get_app()
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main() 