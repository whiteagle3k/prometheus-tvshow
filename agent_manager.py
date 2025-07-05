# extensions/tvshow/agent_manager.py
import time
import logging
from typing import Dict, Any, Optional

from core.exolink.router import router
from core.exolink.models import SourceType, TargetType, ExchangeType

class AgentManager:
    def __init__(self, agent_registry):
        self.agent_registry = agent_registry
        self.logger = logging.getLogger("TVShowAgentManager")

    async def route_message_to_agent(self, agent_id, user_message, *, context=None, metadata=None):
        """Route a message to an agent using ExoLink pipeline."""
        if agent_id not in self.agent_registry:
            raise ValueError(f"Agent {agent_id} not found")
        
        start_time = time.time()
        try:
            # Use ExoLink router to send message to agent
            result = router.send(
                content=user_message,
                source="tvshow:user",
                target=f"entity:{agent_id}",
                exchange_type=ExchangeType.TEXT,
                metadata={
                    "context": context,
                    "original_metadata": metadata,
                    "source": "tvshow_extension"
                }
            )
            
            elapsed = time.time() - start_time
            self.logger.info(f"Agent {agent_id} responded via ExoLink in {elapsed:.2f}s")
            
            return {
                "response": result,
                "agent_id": agent_id,
                "elapsed": elapsed,
                "context": context,
                "metadata": metadata,
                "routed_via": "exolink"
            }
        except Exception as e:
            self.logger.error(f"Error routing message to {agent_id} via ExoLink: {e}")
            # Fallback to direct think() if ExoLink fails
            try:
                agent = self.agent_registry[agent_id]
                response = await agent.think(user_message)
                elapsed = time.time() - start_time
                self.logger.warning(f"Agent {agent_id} responded via direct think() in {elapsed:.2f}s (ExoLink failed)")
                return {
                    "response": response,
                    "agent_id": agent_id,
                    "elapsed": elapsed,
                    "context": context,
                    "metadata": metadata,
                    "routed_via": "direct_fallback"
                }
            except Exception as fallback_error:
                self.logger.error(f"Both ExoLink and direct think() failed for {agent_id}: {fallback_error}")
                return {
                    "error": str(fallback_error),
                    "agent_id": agent_id,
                    "context": context,
                    "metadata": metadata,
                    "routed_via": "failed"
                } 