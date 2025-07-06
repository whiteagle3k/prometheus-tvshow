"""
TV Show Router

Provides API endpoints for the TV show simulation, including character management,
scenario injection, and chat functionality.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Dict, List, Any, Optional
import asyncio
import json
import os
import random

from .entities import get_character, get_all_characters
from .scenarios import ScenarioManager, create_sample_scenarios
from .reflector import reflector  # Use the global singleton

# Import Prometheus registry system
from core.runtime.registry import register_entity_class, get_agent
from core.runtime.lifecycle import startup_system
# Add imports for AgentManager and ChatContextBuilder
from .agent_manager import AgentManager
from .context_builder import ChatContextBuilder


class TVShowRouter:
    """Router for TV show extension API endpoints."""
    
    def __init__(self):
        self.app = FastAPI(title="TV Show Extension", version="0.1.0")
        self.characters: Dict[str, Any] = {}
        self.scenario_manager = ScenarioManager()
        self.chat_history: List[Dict[str, Any]] = []
        self._autonomy_task = None
        self.reflector = reflector  # Use the global singleton
        self.ws_clients = set()  # Set of connected WebSocket clients
        # AgentManager and ContextBuilder
        self.agent_manager = AgentManager(self.characters)
        self.context_builder = ChatContextBuilder(self.reflector, self.scenario_manager)
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

        # Register ExoLink targets for each character (must be after self.characters is populated)
        from core.exolink.router import router
        from core.exolink.models import TargetType
        def make_character_handler(character):
            async def handler(exchange):
                import asyncio
                if asyncio.iscoroutinefunction(character.think):
                    return await character.think(exchange.content)
                else:
                    return character.think(exchange.content)
            return handler
        for character_id, character in self.characters.items():
            router.register_target(TargetType.ENTITY, character_id, make_character_handler(character))

    async def _broadcast_event(self, event: dict):
        #print(f"[DEBUG] Broadcasting event: {event}")
        """Broadcast an event to all connected WebSocket clients."""
        to_remove = set()
        for ws in self.ws_clients:
            try:
                await ws.send_json(event)
            except Exception:
                to_remove.add(ws)
        self.ws_clients -= to_remove

    async def _send_initial_state(self, ws):
        """Send the latest state for all event types to a new client."""
        try:
            # Chat
            await ws.send_json({"type": "chat", "payload": {"history": self.chat_history[-50:]}})
            # Mood
            moods = {cid: char.get_mood() for cid, char in self.characters.items()}
            await ws.send_json({"type": "mood", "payload": moods})
            # Memory
            for cid, char in self.characters.items():
                await ws.send_json({"type": "memory", "payload": {"character_id": cid, "log": char.get_memory_log()}})
            # Scene
            scene_summary = self.reflector.get_current_scene_summary()
            if scene_summary:
                await ws.send_json({"type": "scene", "payload": scene_summary.to_dict()})
            # Narrative
            arcs = list(self.scenario_manager.get_all_narrative_arcs())
            await ws.send_json({"type": "narrative", "payload": arcs})
            # Characters (NEW)
            char_list = []
            for cid, char in self.characters.items():
                char_info = {
                    "id": cid,
                    "name": getattr(char, 'CHARACTER_NAME', cid),
                    "description": getattr(char, 'CHARACTER_DESCRIPTION', ""),
                    "status": "running" if hasattr(char, 'is_running') and char.is_running else "initialized",
                    "initialized": True
                }
                char_list.append(char_info)
            await ws.send_json({"type": "characters", "payload": char_list})
            # Scenarios (NEW)
            scenarios = []
            for scenario in self.scenario_manager.get_all_scenarios():
                scenarios.append({
                    "scenario_id": getattr(scenario, 'scenario_id', None),
                    "title": getattr(scenario, 'title', ""),
                    "description": getattr(scenario, 'description', ""),
                    "executed": getattr(scenario, 'executed', False)
                })
            await ws.send_json({"type": "scenarios", "payload": scenarios})
            # Status (NEW)
            status = {
                "status": "running",
                "characters_initialized": len(self.characters),
                "total_characters": len(get_all_characters()),
                "active_scenarios": len(self.scenario_manager.get_active_scenarios()),
                "total_messages": len(self.chat_history),
                "scenarios_executed": len(self.scenario_manager.get_scenario_history())
            }
            await ws.send_json({"type": "status", "payload": status})
        except Exception as e:
            print(f"[WebSocket Initial State Error] {e}")
            import traceback; traceback.print_exc()
            raise

    async def _trigger_character_reply(self, character_id, user_message):
        """Trigger a direct, context-rich reply from the specified character to a user message."""
        if character_id not in self.characters:
            return
        character = self.characters[character_id]
        # Gather context
        scene_context = self.reflector.get_scene_context_for_character(character_id)
        arc_context = self.scenario_manager.get_current_arc_context()
        # Build a prompt as a direct reply to the user
        if hasattr(character, 'generate_autonomous_message'):
            prompt = await character.generate_autonomous_message(
                scene_context=scene_context,
                arc_context=arc_context,
                user_message=user_message
            )
        else:
            prompt = user_message
        response_data = await character.think(prompt)
        ai_response = response_data.get("response", prompt)
        if isinstance(ai_response, dict) and "content" in ai_response:
            ai_response = ai_response["content"]
        cleaned = ai_response.replace(prompt, "").strip()
        ai_chat_entry = {
            "character_id": character_id,
            "content": cleaned,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.chat_history.append(ai_chat_entry)
        asyncio.create_task(self._broadcast_event({"type": "chat", "payload": {"message": ai_chat_entry}}))
        # Log to character memory, Reflector, etc. as needed
        character.log_message("user", "user", user_message)
        self.reflector.add_message(character_id, cleaned, "autonomous")
        # Broadcast memory and scene updates
        asyncio.create_task(self._broadcast_event({"type": "memory", "payload": {"character_id": character_id, "log": character.get_memory_log()}}))
        scene_summary = self.reflector.get_current_scene_summary()
        if scene_summary:
            asyncio.create_task(self._broadcast_event({"type": "scene", "payload": scene_summary.to_dict()}))

    def _setup_routes(self):
        """Setup API routes."""
        
        # Add startup event to auto-initialize characters and start autonomy loop
        @self.app.on_event("startup")
        async def startup_event():
            await self._auto_initialize_characters()
            # REMOVE: Do not start background autonomy loop
            # if not self._autonomy_task:
            #     self._autonomy_task = asyncio.create_task(self._autonomous_character_loop())
        
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
            print(f"[DEBUG] /tvshow/chat handler called with: {message}")
            """Send a message to the chat and get AI response."""
            character_id = message.get("character_id")
            content = message.get("content")
            if not content:
                raise HTTPException(status_code=400, detail="content is required")
            # Build context for this message
            context = self.context_builder.build_context(character_id, content)
            arc_id = context.get("arc_id")
            phase_id = context.get("phase_id")
            timestamp = asyncio.get_event_loop().time()
            # If no character_id, treat as scene message (no agent response)
            if not character_id:
                scene_chat_entry = {
                    "character_id": "scene",
                    "content": content,
                    "timestamp": timestamp,
                    "arc_id": arc_id,
                    "phase_id": phase_id
                }
                self.chat_history.append(scene_chat_entry)
                print(f"[DEBUG] Appending and broadcasting scene message: {scene_chat_entry}")
                asyncio.create_task(self._broadcast_event({"type": "chat", "payload": {"message": scene_chat_entry}}))
                self.reflector.add_message("scene", content, "scene")
                # Still check for arc/scenario triggers
                triggered_arcs = self.scenario_manager.check_arc_triggers(content, "scene")
                for arc in triggered_arcs:
                    self.scenario_manager.activate_narrative_arc(arc.arc_id)
                triggered_scenarios = self.scenario_manager.check_triggers(content, "scene")
                # Update arcs with context
                scene_context = {
                    "scene_content": content,
                    "active_characters": ["scene"]
                }
                arc_transitions = self.scenario_manager.update_narrative_arcs(scene_context)
                # Broadcast scene/narrative updates
                scene_summary = self.reflector.get_current_scene_summary()
                if scene_summary:
                    asyncio.create_task(self._broadcast_event({"type": "scene", "payload": scene_summary.to_dict()}))
                arcs = list(self.scenario_manager.get_all_narrative_arcs())
                asyncio.create_task(self._broadcast_event({"type": "narrative", "payload": arcs}))
                return {"status": "success", "message": "Scene message logged", "scene_message": scene_chat_entry}
            # Otherwise, normal agent message
            user_chat_entry = {
                "character_id": "user",
                "content": content,
                "timestamp": timestamp,
                "arc_id": arc_id,
                "phase_id": phase_id
            }
            self.chat_history.append(user_chat_entry)
            print(f"[DEBUG] Appending and broadcasting user message: {user_chat_entry}")
            asyncio.create_task(self._broadcast_event({"type": "chat", "payload": {"message": user_chat_entry}}))
            self.characters[character_id].log_message("user", "user", content)
            self.reflector.add_message("user", content, "user")
            triggered_arcs = self.scenario_manager.check_arc_triggers(content, character_id)
            for arc in triggered_arcs:
                self.scenario_manager.activate_narrative_arc(arc.arc_id)
            # Route message to agent via AgentManager
            agent_result = await self.agent_manager.route_message_to_agent(
                character_id, content, context=context, metadata=None
            )
            ai_response = agent_result.get("response")
            if isinstance(ai_response, dict) and "content" in ai_response:
                ai_response = ai_response["content"]
            ai_chat_entry = {
                "character_id": character_id,
                "content": ai_response,
                "timestamp": asyncio.get_event_loop().time(),
                "arc_id": arc_id,
                "phase_id": phase_id
            }
            self.chat_history.append(ai_chat_entry)
            print(f"[DEBUG] Appending and broadcasting AI message: {ai_chat_entry}")
            asyncio.create_task(self._broadcast_event({"type": "chat", "payload": {"message": ai_chat_entry}}))
            self.characters[character_id].log_message(character_id, "ai", ai_response)
            self.reflector.add_message(character_id, ai_response, "ai")
            triggered_scenarios = self.scenario_manager.check_triggers(content, character_id)
            scene_context = {
                "scene_content": content + " " + str(ai_response),
                "active_characters": [character_id, "user"]
            }
            arc_transitions = self.scenario_manager.update_narrative_arcs(scene_context)
            asyncio.create_task(self._broadcast_event({"type": "memory", "payload": {"character_id": character_id, "log": self.characters[character_id].get_memory_log()}}))
            scene_summary = self.reflector.get_current_scene_summary()
            if scene_summary:
                asyncio.create_task(self._broadcast_event({"type": "scene", "payload": scene_summary.to_dict()}))
            arcs = list(self.scenario_manager.get_all_narrative_arcs())
            asyncio.create_task(self._broadcast_event({"type": "narrative", "payload": arcs}))
            return {
                "status": "success",
                "message": "Message sent and AI responded",
                "user_message": user_chat_entry,
                "ai_response": ai_chat_entry,
                "triggered_scenarios": [s.scenario_id for s in triggered_scenarios],
                "triggered_arcs": [arc.arc_id for arc in triggered_arcs],
                "arc_transitions": arc_transitions
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
        
        @self.app.get("/tvshow/scenarios/arcs")
        async def get_narrative_arcs():
            """Get all available narrative arcs."""
            arcs = []
            for arc in self.scenario_manager.get_all_narrative_arcs():
                arcs.append(arc.to_dict())
            return {"arcs": arcs}
        
        @self.app.post("/tvshow/scenarios/arcs/{arc_id}/activate")
        async def activate_narrative_arc(arc_id: str):
            """Activate a narrative arc."""
            success = self.scenario_manager.activate_narrative_arc(arc_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"Narrative arc {arc_id} not found or already active")
            
            return {
                "status": "success",
                "message": f"Narrative arc {arc_id} activated"
            }
        
        @self.app.post("/tvshow/scenarios/arcs/{arc_id}/deactivate")
        async def deactivate_narrative_arc(arc_id: str):
            """Deactivate a narrative arc."""
            success = self.scenario_manager.deactivate_narrative_arc(arc_id)
            if not success:
                raise HTTPException(status_code=404, detail=f"Narrative arc {arc_id} not found or not active")
            
            return {
                "status": "success",
                "message": f"Narrative arc {arc_id} deactivated"
            }
        
        @self.app.get("/tvshow/scenarios/arcs/status")
        async def get_arcs_status():
            """Get status of all narrative arcs."""
            return {
                "all_arcs": self.scenario_manager.get_all_arcs_status(),
                "active_arcs": [arc.to_dict() for arc in self.scenario_manager.get_active_arcs()],
                "arc_history": self.scenario_manager.get_arc_history()
            }
        
        @self.app.get("/tvshow/scenarios/arcs/context")
        async def get_arcs_context():
            """Get current narrative arc context."""
            return {
                "arc_context": self.scenario_manager.get_current_arc_context()
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

        @self.app.get("/tvshow/logs/{character_id}")
        async def get_character_log(character_id: str):
            if character_id not in self.characters:
                raise HTTPException(status_code=404, detail=f"Character {character_id} not initialized")
            return {"log": self.characters[character_id].get_memory_log()}
        
        @self.app.get("/tvshow/scene/summary")
        async def get_scene_summary():
            """Get current scene summary."""
            current_summary = self.reflector.get_current_scene_summary()
            if current_summary:
                return current_summary.to_dict()
            return {"message": "No scene summary available yet"}
        
        @self.app.get("/tvshow/scene/log")
        async def get_scene_log():
            """Get full scene conversation log."""
            return {
                "log": self.reflector.get_full_log(),
                "stats": self.reflector.get_scene_stats()
            }
        
        @self.app.get("/tvshow/scene/summaries")
        async def get_scene_summaries():
            """Get all scene summaries."""
            return {
                "summaries": self.reflector.get_summaries()
            }
        
        @self.app.get("/tvshow/characters/{character_id}/mood")
        async def get_character_mood(character_id: str):
            """Get character's current mood state."""
            if character_id not in self.characters:
                raise HTTPException(status_code=404, detail=f"Character {character_id} not initialized")
            
            character = self.characters[character_id]
            return {
                "character_id": character_id,
                "mood": character.get_mood(),
                "mood_state": character.get_mood_state()
            }
        
        @self.app.get("/tvshow/characters/moods")
        async def get_all_character_moods():
            """Get mood states for all characters."""
            moods = {}
            for character_id, character in self.characters.items():
                moods[character_id] = {
                    "mood": character.get_mood(),
                    "mood_state": character.get_mood_state()
                }
            return {"character_moods": moods}
        
        @self.app.post("/tvshow/characters/{character_id}/mood/feedback")
        async def apply_character_mood_feedback(character_id: str, feedback: Dict[str, Any]):
            """Apply emotional feedback to a character's mood."""
            if character_id not in self.characters:
                raise HTTPException(status_code=404, detail=f"Character {character_id} not initialized")
            
            event = feedback.get("event")
            score = feedback.get("score", 0.0)
            
            if not event:
                raise HTTPException(status_code=400, detail="event is required")
            
            character = self.characters[character_id]
            character.apply_emotional_feedback(event, score)
            
            # Broadcast mood update
            asyncio.create_task(self._broadcast_event({"type": "mood", "payload": {character_id: character.get_mood()}}))
            
            return {
                "status": "success",
                "character_id": character_id,
                "event": event,
                "score": score,
                "new_mood": character.get_mood()
            }
        
        @self.app.websocket("/tvshow/ws")
        async def websocket_endpoint(ws: WebSocket):
            await ws.accept()
            self.ws_clients.add(ws)
            try:
                await self._send_initial_state(ws)
                while True:
                    await ws.receive_text()  # Keep connection alive, ignore input
            except WebSocketDisconnect:
                self.ws_clients.discard(ws)
            except Exception:
                self.ws_clients.discard(ws)

    def _register_characters(self):
        """Register TV show characters with Prometheus registry and ExoLink."""
        from core.exolink.router import router
        from core.exolink.models import TargetType
        def make_character_handler(character):
            async def handler(exchange):
                # ExoLink expects a sync handler, so wrap in ensure_future if needed
                import asyncio
                if asyncio.iscoroutinefunction(character.think):
                    return await character.think(exchange.content)
                else:
                    return character.think(exchange.content)
            return handler
        for character_id, character in get_all_characters().items():
            register_entity_class(character_id, character)
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance."""
        return self.app


# Create router instance
router = TVShowRouter()
app = router.get_app() 