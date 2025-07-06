#!/usr/bin/env python3
"""
Test script to verify LocalLLM-based summarization.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from extensions.tvshow.reflector import reflector

async def test_local_llm_summary():
    """Test the LocalLLM-based summarization."""
    print("🧪 Testing LocalLLM Summarization")
    print("=" * 50)
    
    # Add some test messages about beer brewing
    print("\n1. Adding beer brewing conversation...")
    await reflector.add_message("user", "I love beer brewing!", "user")
    await reflector.add_message("marvin", "Ah, beer brewing—the art of transforming water into liquid joy.", "ai")
    await reflector.add_message("max", "It's fascinating how beer brewing combines science and creativity.", "ai")
    await reflector.add_message("leo", "Beer brewing is like poetry in liquid form!", "ai")
    await reflector.add_message("emma", "I want to create a new beer recipe!", "ai")
    
    print(f"\n2. Conversation log has {len(reflector.conversation_log)} messages")
    
    # Test the dialogue summarization
    print("\n3. Testing dialogue summarization...")
    recap = await reflector.summarize_dialogue_with_fastllm(n_messages=5, n_sentences=3)
    print(f"Recap: {recap}")
    
    # Test the scene summary generation
    print("\n4. Testing scene summary generation...")
    summary = await reflector._generate_summary(reflector.conversation_log[-5:])
    print(f"Scene Summary: {summary}")
    
    # Test the full context generation
    print("\n5. Testing full context generation...")
    context = await reflector.get_scene_context_for_character("marvin")
    print(f"Context for Marvin:\n{context[:500]}...")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_local_llm_summary()) 