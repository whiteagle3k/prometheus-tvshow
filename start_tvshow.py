#!/usr/bin/env python3
"""
TV Show Extension Startup Script

Starts the TV show backend server with UI support.
"""

import uvicorn
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from extensions.tvshow.router import app

def main():
    """Start the TV show server."""
    print("🎬 Starting TV Show Extension...")
    print("=" * 50)
    print("📺 TV Show Director Console")
    print("🌐 Backend API: http://localhost:8000")
    print("🎭 UI Console: http://localhost:8000/tvshow")
    print("📋 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    
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