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
import re

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
        await self.reflector.add_message(character_id, cleaned, "autonomous")
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
            # New: support source and destination
            source = message.get("source")
            destination = message.get("destination")
            character_id = message.get("character_id")
            content = message.get("content")
            if not content:
                raise HTTPException(status_code=400, detail="content is required")

            # --- NEW: Regex-based character name detection and splitting ---
            from .entities import get_all_characters
            character_names = list(get_all_characters().keys())
            # Only apply splitting for user/scene messages with no explicit destination
            if (not destination or destination == "all") and (source in [None, "user", "scene", ""]):
                # Regex: look for e.g. "Max," or "Max:"
                pattern = r"(?:^|[.!?]\s+)(%s)[,:\s]" % "|".join([re.escape(name.capitalize()) for name in character_names])
                matches = list(re.finditer(pattern, content))
                if matches:
                    # Split at the first match
                    match = matches[0]
                    split_idx = match.start(1)
                    before = content[:split_idx].strip()
                    after = content[split_idx:].strip()
                    # Do NOT remove the name from 'after'; keep the addressed name in the message content
                    addressed_name = None
                    for name in character_names:
                        if after.lower().startswith(name + ',') or after.lower().startswith(name + ':') or after.lower().startswith(name + ' '):
                            addressed_name = name
                            break
                    results = []
                    if before:
                        # Send general part as scene/all message
                        results.append({
                            "source": source or "user",
                            "destination": "all",
                            "content": before
                        })
                    if addressed_name and after:
                        # Send addressed part as direct message, KEEPING the name in the content
                        results.append({
                            "source": source or "user",
                            "destination": addressed_name,
                            "content": after
                        })
                    # Recursively call send_message for each part
                    responses = []
                    for part in results:
                        # Avoid infinite recursion by setting a flag
                        part["_parsed"] = True
                        resp = await send_message(part)
                        responses.append(resp)
                    return {"status": "split", "parts": responses}
            # --- END SPLIT LOGIC ---

            # --- Character-to-character detection and routing ---
            # Only for character-originated messages, not already parsed, and not direct messages
            if (
                source in self.characters
                and (not message.get('_parsed'))
                and (not destination or destination == 'user' or destination == 'all')
            ):
                # Regex: look for e.g. "Marvin," or "Marvin:"
                pattern = r"(?:^|[.!?]\s+)(%s)[,:\s]" % "|".join([re.escape(name.capitalize()) for name in character_names if name != source])
                matches = list(re.finditer(pattern, content))
                if matches:
                    match = matches[0]
                    # Route the whole message to the addressed character
                    addressed_name = matches[0].group(1).lower()
                    if addressed_name in character_names:
                        print(f"[DEBUG] Character-to-character detected: {source} > {addressed_name}")
                        part = {
                            "source": source,
                            "destination": addressed_name,
                            "content": content,
                            "_parsed": True
                        }
                        resp = await send_message(part)
                        # Optionally, return both the original and the routed message
                        return {"status": "character_to_character", "original": user_chat_entry, "routed": resp}
            # --- END character-to-character logic ---

            context = self.context_builder.build_context(character_id, content)
            arc_id = context.get("arc_id")
            phase_id = context.get("phase_id")
            timestamp = asyncio.get_event_loop().time()
            # If no character_id and no destination, treat as scene message
            if not character_id and not destination:
                scene_chat_entry = {
                    "source": "scene",
                    "destination": "all",
                    "content": content,
                    "timestamp": timestamp,
                    "arc_id": arc_id,
                    "phase_id": phase_id
                }
                self.chat_history.append(scene_chat_entry)
                print(f"[DEBUG] Appending and broadcasting scene message: {scene_chat_entry}")
                asyncio.create_task(self._broadcast_event({"type": "chat", "payload": {"message": scene_chat_entry}}))
                await self.reflector.add_message("scene", content, "scene")
                # Arc/scenario triggers as before
                triggered_arcs = self.scenario_manager.check_arc_triggers(content, "scene")
                for arc in triggered_arcs:
                    self.scenario_manager.activate_narrative_arc(arc.arc_id)
                triggered_scenarios = self.scenario_manager.check_triggers(content, "scene")
                scene_context = {"scene_content": content, "active_characters": ["scene"]}
                arc_transitions = self.scenario_manager.update_narrative_arcs(scene_context)
                scene_summary = self.reflector.get_current_scene_summary()
                if scene_summary:
                    asyncio.create_task(self._broadcast_event({"type": "scene", "payload": scene_summary.to_dict()}))
                arcs = list(self.scenario_manager.get_all_narrative_arcs())
                asyncio.create_task(self._broadcast_event({"type": "narrative", "payload": arcs}))
                return {"status": "success", "message": "Scene message logged", "scene_message": scene_chat_entry}
            # Otherwise, normal message (user or character)
            # Backward compatibility: if only character_id, treat as user->character
            if not source:
                source = "user"
            if not destination:
                destination = character_id
            user_chat_entry = {
                "source": source,
                "destination": destination,
                "content": content,
                "timestamp": timestamp,
                "arc_id": arc_id,
                "phase_id": phase_id
            }
            self.chat_history.append(user_chat_entry)
            print(f"[DEBUG] Appending and broadcasting user/character message: {user_chat_entry}")
            asyncio.create_task(self._broadcast_event({"type": "chat", "payload": {"message": user_chat_entry}}))
            # Log to memory
            if source == "user":
                if destination in self.characters:
                    self.characters[destination].log_message("user", "user", content)
                await self.reflector.add_message("user", content, "user")
            else:
                if source in self.characters:
                    self.characters[source].log_message(source, "ai", content)
                await self.reflector.add_message(source, content, "ai")
            triggered_arcs = self.scenario_manager.check_arc_triggers(content, destination)
            for arc in triggered_arcs:
                self.scenario_manager.activate_narrative_arc(arc.arc_id)
            # Route message to agent via AgentManager (if destination is a character)
            ai_response = None
            ai_chat_entry = None
            if destination in self.characters:
                agent_result = await self.agent_manager.route_message_to_agent(
                    destination, content, context=context, metadata=None
                )
                ai_response = agent_result.get("response")
                if isinstance(ai_response, dict) and "content" in ai_response:
                    ai_response = ai_response["content"]
                ai_chat_entry = {
                    "source": destination,
                    "destination": source,
                    "content": ai_response,
                    "timestamp": asyncio.get_event_loop().time(),
                    "arc_id": arc_id,
                    "phase_id": phase_id
                }
                self.chat_history.append(ai_chat_entry)
                print(f"[DEBUG] Appending and broadcasting AI reply: {ai_chat_entry}")
                asyncio.create_task(self._broadcast_event({"type": "chat", "payload": {"message": ai_chat_entry}}))
                self.characters[destination].log_message(destination, "ai", ai_response)
                
                # --- NEW: Send AI response through ExoLink for Reflector orchestration ---
                from core.exolink import router as exolink_router
                from core.exolink.models import Source, Target, SourceType, TargetType, ExchangeType
                
                # Create ExoLink exchange for AI response
                ai_source = Source(type=SourceType.ENTITY, identifier=destination)
                # Send to the first character as a proxy target - the Reflector will catch it via subscription
                proxy_target = list(self.characters.keys())[0] if self.characters else "max"
                ai_target = Target(type=TargetType.ENTITY, identifier=proxy_target)
                
                # Send through ExoLink - this will trigger Reflector's _handle_character_message
                try:
                    await exolink_router.send(
                        content=ai_response,
                        source=ai_source,
                        target=ai_target,
                        exchange_type=ExchangeType.TEXT,
                        metadata={"_ai_response": True, "_original_user": source, "_proxy_target": True}
                    )
                    print(f"[DEBUG] Sent AI response through ExoLink: {destination} > {proxy_target}")
                except Exception as e:
                    print(f"[DEBUG] ExoLink send failed: {e}")
                
                # Remove redundant add_message call - Reflector will handle this via ExoLink subscription
                # await self.reflector.add_message(destination, ai_response, "ai")

                # --- Character-to-character detection for AI replies ---
                # Only if not already parsed, and not direct message
                ai_response_str = ai_response
                if isinstance(ai_response, dict) and 'response' in ai_response:
                    ai_response_str = ai_response['response']
                if (
                    not message.get('_parsed')
                    and (source != destination)
                    and isinstance(ai_response_str, str)
                ):
                    pattern = r"(?:^|[.!?]\s+)(%s)[,:\s]" % "|".join([re.escape(name.capitalize()) for name in character_names if name != destination])
                    matches = list(re.finditer(pattern, ai_response_str))
                    if matches:
                        match = matches[0]
                        addressed_name = matches[0].group(1).lower()
                        if addressed_name in character_names:
                            print(f"[DEBUG] Character-to-character detected in AI reply: {destination} > {addressed_name}")
                            part = {
                                "source": destination,
                                "destination": addressed_name,
                                "content": ai_response_str,
                                "_parsed": True
                            }
                            resp = await send_message(part)
                            # Optionally, return both the original and the routed message
                            return {"status": "character_to_character", "original": ai_chat_entry, "routed": resp}
                # --- END character-to-character logic for AI replies ---

            triggered_scenarios = self.scenario_manager.check_triggers(content, destination)
            scene_context = {"scene_content": content + (" " + str(ai_response) if ai_response else ""), "active_characters": [source, destination]}
            arc_transitions = self.scenario_manager.update_narrative_arcs(scene_context)
            if destination in self.characters:
                asyncio.create_task(self._broadcast_event({
                    "type": "memory",
                    "payload": {"character_id": destination, "log": self.characters[destination].get_memory_log()}
                }))
            scene_summary = self.reflector.get_current_scene_summary()
            if scene_summary:
                asyncio.create_task(self._broadcast_event({"type": "scene", "payload": scene_summary.to_dict()}))
            arcs = list(self.scenario_manager.get_all_narrative_arcs())
            asyncio.create_task(self._broadcast_event({"type": "narrative", "payload": arcs}))
            return {
                "status": "success",
                "message": "Message sent and AI responded" if ai_response else "Message sent",
                "user_message": user_chat_entry,
                "ai_response": ai_chat_entry if ai_response else None,
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