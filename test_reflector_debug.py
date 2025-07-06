#!/usr/bin/env python3
"""
Test script to debug the reflector functions.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from extensions.tvshow.reflector import reflector

async def test_reflector():
    """Test the reflector functions."""
    print("🧪 Testing Reflector Debug Functions")
    print("=" * 50)
    
    # Add some test messages
    print("\n1. Adding test messages...")
    reflector.add_message("user", "Hello everyone!", "user")
    reflector.add_message("max", "Hi there! How are you?", "ai")
    reflector.add_message("marvin", "Oh, another day of existence.", "ai")
    reflector.add_message("leo", "What a beautiful day!", "ai")
    reflector.add_message("emma", "I love creativity!", "ai")
    
    print(f"\n2. Conversation log has {len(reflector.conversation_log)} messages")
    print(f"3. Scene summaries: {len(reflector.scene_summaries)}")
    
    # Test the summarize function
    print("\n4. Testing summarize_dialogue_with_fastllm...")
    try:
        recap = await reflector.summarize_dialogue_with_fastllm(n_messages=5, n_sentences=3)
        print(f"Recap result: {recap}")
    except Exception as e:
        print(f"Error in summarization: {e}")
    
    # Test the scene context function
    print("\n5. Testing get_scene_context_for_character...")
    try:
        context = await reflector.get_scene_context_for_character("marvin")
        print(f"Context result: {context[:300]}...")
    except Exception as e:
        print(f"Error in context generation: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_reflector()) 