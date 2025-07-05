"""
TV Show Router

Provides API endpoints for the TV show simulation, including character management,
scenario injection, and chat functionality.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, List, Any, Optional
import asyncio
import json
import os

from .entities import get_character, get_all_characters
from .scenarios import ScenarioManager, create_sample_scenarios


class TVShowRouter:
    """Router for TV show extension API endpoints."""
    
    def __init__(self):
        self.app = FastAPI(title="TV Show Extension", version="0.1.0")
        self.characters: Dict[str, Any] = {}
        self.scenario_manager = ScenarioManager()
        self.chat_history: List[Dict[str, Any]] = []
        
        # Initialize sample scenarios
        for scenario in create_sample_scenarios():
            self.scenario_manager.add_scenario(scenario)
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        # Serve UI static files
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "dist")
        if os.path.exists(ui_path):
            self.app.mount("/tvshow/ui", StaticFiles(directory=ui_path), name="ui")
        
        @self.app.get("/tvshow")
        async def serve_ui():
            """Serve the main UI."""
            ui_index = os.path.join(ui_path, "index.html")
            if os.path.exists(ui_index):
                return FileResponse(ui_index)
            return {"message": "UI not built yet. Run 'npm run build' in ui/ directory"}
        
        @self.app.get("/tvshow/ping")
        async def ping():
            """Health check endpoint."""
            return {"status": "ok", "message": "TV Show Extension is running"}
        
        @self.app.get("/tvshow/characters")
        async def get_characters():
            """Get all available characters."""
            character_list = []
            for name, entity_class in get_all_characters().items():
                character_list.append({
                    "id": name,
                    "name": entity_class.__name__,
                    "description": entity_class.__doc__
                })
            return {"characters": character_list}
        
        @self.app.post("/tvshow/characters/{character_id}/init")
        async def init_character(character_id: str):
            """Initialize a character."""
            entity_class = get_character(character_id)
            if not entity_class:
                raise HTTPException(status_code=404, detail=f"Character {character_id} not found")
            
            try:
                character = entity_class()
                self.characters[character_id] = character
                return {
                    "status": "success",
                    "character_id": character_id,
                    "message": f"Character {character_id} initialized"
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to initialize character: {str(e)}")
        
        @self.app.get("/tvshow/characters/{character_id}/status")
        async def get_character_status(character_id: str):
            """Get character status."""
            if character_id not in self.characters:
                raise HTTPException(status_code=404, detail=f"Character {character_id} not initialized")
            
            character = self.characters[character_id]
            return {
                "character_id": character_id,
                "status": "active",
                "identity": character.identity_config
            }
        
        @self.app.post("/tvshow/chat")
        async def send_message(message: Dict[str, Any]):
            """Send a message to the chat."""
            character_id = message.get("character_id")
            content = message.get("content")
            
            if not character_id or not content:
                raise HTTPException(status_code=400, detail="character_id and content are required")
            
            if character_id not in self.characters:
                raise HTTPException(status_code=404, detail=f"Character {character_id} not initialized")
            
            # Add message to chat history
            chat_entry = {
                "character_id": character_id,
                "content": content,
                "timestamp": asyncio.get_event_loop().time()
            }
            self.chat_history.append(chat_entry)
            
            # Check for scenario triggers
            triggered_scenarios = self.scenario_manager.check_triggers(content, character_id)
            
            return {
                "status": "success",
                "message": "Message sent",
                "chat_entry": chat_entry,
                "triggered_scenarios": [s.scenario_id for s in triggered_scenarios]
            }
        
        @self.app.get("/tvshow/chat/history")
        async def get_chat_history(limit: int = 50):
            """Get chat history."""
            return {
                "history": self.chat_history[-limit:],
                "total_messages": len(self.chat_history)
            }
        
        @self.app.get("/tvshow/scenarios")
        async def get_scenarios():
            """Get all scenarios."""
            scenarios = []
            for scenario in self.scenario_manager.get_all_scenarios():
                scenarios.append(scenario.to_dict())
            return {"scenarios": scenarios}
        
        @self.app.post("/tvshow/scenarios/{scenario_id}/activate")
        async def activate_scenario(scenario_id: str):
            """Activate a scenario."""
            success = self.scenario_manager.activate_scenario(scenario_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found or already active")
            
            return {
                "status": "success",
                "message": f"Scenario {scenario_id} activated"
            }
        
        @self.app.post("/tvshow/scenarios/{scenario_id}/deactivate")
        async def deactivate_scenario(scenario_id: str):
            """Deactivate a scenario."""
            success = self.scenario_manager.deactivate_scenario(scenario_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} not found or not active")
            
            return {
                "status": "success",
                "message": f"Scenario {scenario_id} deactivated"
            }
        
        @self.app.post("/tvshow/scenarios/{scenario_id}/execute")
        async def execute_scenario(scenario_id: str):
            """Execute a scenario."""
            result = self.scenario_manager.execute_scenario(scenario_id)
            if "error" in result:
                raise HTTPException(status_code=400, detail=result["error"])
            
            return result
        
        @self.app.get("/tvshow/scenarios/history")
        async def get_scenario_history():
            """Get scenario execution history."""
            return {
                "history": self.scenario_manager.get_scenario_history()
            }
        
        @self.app.get("/tvshow/status")
        async def get_show_status():
            """Get overall show status."""
            return {
                "status": "running",
                "characters_initialized": len(self.characters),
                "total_characters": len(get_all_characters()),
                "active_scenarios": len(self.scenario_manager.get_active_scenarios()),
                "total_messages": len(self.chat_history),
                "scenarios_executed": len(self.scenario_manager.get_scenario_history())
            }
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance."""
        return self.app


# Create router instance
router = TVShowRouter()
app = router.get_app() 