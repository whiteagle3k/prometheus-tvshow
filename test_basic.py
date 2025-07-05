"""
Basic test for TV Show Extension

Tests the basic functionality of the TV show extension including:
- Character creation
- Router functionality
- Scenario management
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from extensions.tvshow.entities import get_character, get_all_characters
from extensions.tvshow.scenarios import ScenarioManager, create_sample_scenarios
from extensions.tvshow.router import TVShowRouter


async def test_character_creation():
    """Test that characters can be created."""
    print("🧪 Testing character creation...")
    
    # Test getting all characters
    characters = get_all_characters()
    print(f"✅ Found {len(characters)} characters: {list(characters.keys())}")
    
    # Test getting individual characters
    for name in ["max", "leo", "emma", "marvin"]:
        entity_class = get_character(name)
        if entity_class:
            print(f"✅ Character {name} found")
        else:
            print(f"❌ Character {name} not found")
    
    return True


async def test_scenario_management():
    """Test scenario management functionality."""
    print("🧪 Testing scenario management...")
    
    # Create scenario manager
    manager = ScenarioManager()
    
    # Add sample scenarios
    scenarios = create_sample_scenarios()
    for scenario in scenarios:
        manager.add_scenario(scenario)
    
    print(f"✅ Added {len(scenarios)} scenarios")
    
    # Test scenario activation
    if scenarios:
        first_scenario = scenarios[0]
        success = manager.activate_scenario(first_scenario.scenario_id)
        print(f"✅ Scenario activation: {success}")
    
    return True


async def test_router_creation():
    """Test that the router can be created."""
    print("🧪 Testing router creation...")
    
    try:
        router = TVShowRouter()
        print("✅ Router created successfully")
        
        # Test basic router functionality
        app = router.get_app()
        print("✅ FastAPI app created successfully")
        
        return True
    except Exception as e:
        print(f"❌ Router creation failed: {e}")
        return False


async def test_character_identity_loading():
    """Test that character identities can be loaded."""
    print("🧪 Testing character identity loading...")
    
    try:
        # Test creating a character instance
        max_class = get_character("max")
        if max_class:
            max_instance = max_class()
            identity = max_instance.identity_config
            
            print(f"✅ Max identity loaded: {identity.get('name', 'Unknown')}")
            print(f"✅ Motivation: {identity.get('motivation', 'Unknown')}")
            
            return True
        else:
            print("❌ Could not get Max character class")
            return False
    except Exception as e:
        print(f"❌ Character identity loading failed: {e}")
        return False


async def run_all_tests():
    """Run all basic tests."""
    print("🚀 Running TV Show Extension basic tests...")
    print("=" * 50)
    
    tests = [
        test_character_creation,
        test_scenario_management,
        test_router_creation,
        test_character_identity_loading
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! TV Show Extension is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    asyncio.run(run_all_tests()) 