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

# Import Prometheus registry system
from core.runtime.registry import register_entity_class, get_agent
from core.runtime.lifecycle import startup_system


class TVShowRouter:
    """Router for TV show extension API endpoints."""
    
    def __init__(self):
        self.app = FastAPI(title="TV Show Extension", version="0.1.0")
        self.characters: Dict[str, Any] = {}
        self.scenario_manager = ScenarioManager()
        self.chat_history: List[Dict[str, Any]] = []
        
        # Register TV show characters with Prometheus registry
        self._register_characters()
        
        # Initialize sample scenarios
        for scenario in create_sample_scenarios():
            self.scenario_manager.add_scenario(scenario)
        
        # Setup routes
        self._setup_routes()
    
    async def _auto_initialize_characters(self):
        """Auto-initialize all characters on startup."""
        print("🎭 Auto-initializing all TV show characters...")
        
        for character_id in get_all_characters().keys():
            try:
                character = await get_agent(character_id)
                self.characters[character_id] = character
                print(f"✅ Auto-initialized: {character_id}")
            except Exception as e:
                print(f"❌ Failed to auto-initialize {character_id}: {str(e)}")
        
        print(f"🎭 Auto-initialization complete. {len(self.characters)} characters ready.")
    
    def _setup_routes(self):
        """Setup API routes."""
        
        # Add startup event to auto-initialize characters
        @self.app.on_event("startup")
        async def startup_event():
            await self._auto_initialize_characters()
        
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
                initialized = name in self.characters
                character_list.append({
                    "id": name,
                    "name": entity_class.__name__,
                    "description": entity_class.__doc__,
                    "initialized": initialized,
                    "status": "running" if initialized else "not_initialized"
                })
            return {"characters": character_list}
        
        @self.app.post("/tvshow/characters/{character_id}/init")
        async def init_character(character_id: str):
            """Initialize a character using Prometheus registry."""
            try:
                # Use Prometheus registry to get/initialize the character
                character = await get_agent(character_id)
                self.characters[character_id] = character
                
                return {
                    "status": "success",
                    "character_id": character_id,
                    "message": f"Character {character_id} initialized via Prometheus registry"
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
            """Send a message to the chat and get AI response."""
            character_id = message.get("character_id")
            content = message.get("content")
            
            if not character_id or not content:
                raise HTTPException(status_code=400, detail="character_id and content are required")
            
            if character_id not in self.characters:
                raise HTTPException(status_code=404, detail=f"Character {character_id} not initialized")
            
            # Add user message to chat history
            user_chat_entry = {
                "character_id": "user",
                "content": content,
                "timestamp": asyncio.get_event_loop().time()
            }
            self.chat_history.append(user_chat_entry)
            
            # Get AI response from the character
            character = self.characters[character_id]
            try:
                # Call the character's think method directly instead of process_query
                response_data = await character.think(content)
                ai_response = response_data.get("response", "I'm not sure how to respond to that.")
                if isinstance(ai_response, dict) and "content" in ai_response:
                    ai_response = ai_response["content"]
                
                # Add AI response to chat history
                ai_chat_entry = {
                    "character_id": character_id,
                    "content": ai_response,
                    "timestamp": asyncio.get_event_loop().time()
                }
                self.chat_history.append(ai_chat_entry)
                
                # Check for scenario triggers
                triggered_scenarios = self.scenario_manager.check_triggers(content, character_id)
                
                return {
                    "status": "success",
                    "message": "Message sent and AI responded",
                    "user_message": user_chat_entry,
                    "ai_response": ai_chat_entry,
                    "triggered_scenarios": [s.scenario_id for s in triggered_scenarios]
                }
                
            except Exception as e:
                # Add error response to chat history
                error_chat_entry = {
                    "character_id": character_id,
                    "content": f"Sorry, I'm having trouble responding right now. Error: {str(e)}",
                    "timestamp": asyncio.get_event_loop().time()
                }
                self.chat_history.append(error_chat_entry)
                
                return {
                    "status": "error",
                    "message": f"Failed to get AI response: {str(e)}",
                    "user_message": user_chat_entry,
                    "ai_response": error_chat_entry,
                    "triggered_scenarios": []
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
    
    def _register_characters(self):
        """Register TV show characters with the Prometheus registry."""
        print("🎭 Registering TV show characters with Prometheus registry...")
        
        # Register each character
        characters = get_all_characters()
        for character_id, entity_class in characters.items():
            # Get character info for registration
            temp_instance = entity_class()
            identity = temp_instance.identity_config
            
            register_entity_class(
                entity_id=character_id,
                entity_class=entity_class,
                entity_name=identity.get("name", character_id),
                description=identity.get("description", f"TV Show character: {character_id}")
            )
            
            print(f"✅ Registered character: {character_id} ({identity.get('name', character_id)})")
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance."""
        return self.app


# Create router instance
router = TVShowRouter()
app = router.get_app() 