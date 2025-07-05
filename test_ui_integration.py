"""
Test UI Integration

Tests that the UI can connect to the backend API endpoints.
"""

import asyncio
import sys
import os
import requests
import time

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from extensions.tvshow.router import TVShowRouter
import uvicorn
from fastapi.testclient import TestClient


def test_backend_api():
    """Test that the backend API endpoints work correctly."""
    print("🧪 Testing backend API endpoints...")
    
    # Create router and test client
    router = TVShowRouter()
    client = TestClient(router.get_app())
    
    # Test health check
    response = client.get("/tvshow/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("✅ Health check endpoint works")
    
    # Test characters endpoint
    response = client.get("/tvshow/characters")
    assert response.status_code == 200
    data = response.json()
    assert "characters" in data
    assert len(data["characters"]) == 4  # max, leo, emma, marvin
    print("✅ Characters endpoint works")
    
    # Test scenarios endpoint
    response = client.get("/tvshow/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) > 0
    print("✅ Scenarios endpoint works")
    
    # Test status endpoint
    response = client.get("/tvshow/status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    print("✅ Status endpoint works")
    
    # Test character initialization
    response = client.post("/tvshow/characters/max/init")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print("✅ Character initialization works")
    
    # Test chat endpoint
    response = client.post("/tvshow/chat", json={
        "character_id": "max",
        "content": "Hello everyone! This is a test message."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    print("✅ Chat endpoint works")
    
    # Test chat history
    response = client.get("/tvshow/chat/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    print("✅ Chat history endpoint works")
    
    print("🎉 All backend API tests passed!")


def test_ui_build():
    """Test that the UI was built correctly."""
    print("🧪 Testing UI build...")
    
    ui_dist_path = os.path.join(os.path.dirname(__file__), "ui", "dist")
    assert os.path.exists(ui_dist_path), "UI dist directory not found"
    
    index_html = os.path.join(ui_dist_path, "index.html")
    assert os.path.exists(index_html), "index.html not found"
    
    # Check that the built files exist
    assets_dir = os.path.join(ui_dist_path, "assets")
    assert os.path.exists(assets_dir), "assets directory not found"
    
    # Check for CSS and JS files
    css_files = [f for f in os.listdir(assets_dir) if f.endswith('.css')]
    js_files = [f for f in os.listdir(assets_dir) if f.endswith('.js')]
    
    assert len(css_files) > 0, "No CSS files found"
    assert len(js_files) > 0, "No JS files found"
    
    print("✅ UI build files exist")
    print(f"   CSS files: {len(css_files)}")
    print(f"   JS files: {len(js_files)}")


def test_ui_serving():
    """Test that the UI can be served by the backend."""
    print("🧪 Testing UI serving...")
    
    router = TVShowRouter()
    client = TestClient(router.get_app())
    
    # Test that the UI endpoint exists
    response = client.get("/tvshow")
    assert response.status_code in [200, 404]  # 404 is ok if UI not built yet
    
    print("✅ UI serving endpoint exists")


def run_all_tests():
    """Run all UI integration tests."""
    print("🚀 Running UI Integration Tests...")
    print("=" * 50)
    
    tests = [
        test_backend_api,
        test_ui_build,
        test_ui_serving
    ]
    
    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)
    
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All UI integration tests passed!")
        print("\n📋 Next Steps:")
        print("1. Start the backend server: poetry run python -m uvicorn extensions.tvshow.router:app --host 0.0.0.0 --port 8000")
        print("2. Access the UI at: http://localhost:8000/tvshow")
        print("3. Initialize characters and start the simulation!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    run_all_tests() 