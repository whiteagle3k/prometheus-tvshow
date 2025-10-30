import asyncio
from typing import Optional


class VoiceNarrator:
    """Lightweight voice narrator wrapper.

    Attempts to route TTS via an MCP client if available; otherwise falls back to stdout logging.
    This keeps the feature non-breaking and fully mockable in tests.
    """

    def __init__(self, mcp_url: str = "http://localhost:8080") -> None:
        self._mcp_url = mcp_url
        self._mcp_client = None  # Lazy-init to avoid import-time side-effects

    def _ensure_client(self) -> None:
        if self._mcp_client is not None:
            return
        try:
            # Prefer a generic MCP client import pathway if available in the environment
            from mcp import MCPClient  # type: ignore

            self._mcp_client = MCPClient(base_url=self._mcp_url)
        except Exception:
            # No MCP available; keep None to use stdout fallback
            self._mcp_client = None

    async def speak(self, text: str, voice: str = "alloy", response_format: str = "wav") -> None:
        """Speak text via MCP TTS if available, otherwise log.

        The method is intentionally resilient; failures should not crash demo mode.
        """
        self._ensure_client()
        if not text:
            return

        if self._mcp_client is None:
            print(f"[VOICE:{voice.upper()}] {text}")
            return

        try:
            # Minimal contract: an async tts method with basic kwargs
            await self._mcp_client.tts(
                text=text,
                voice=voice,
                response_format=response_format,
            )
            print(f"[VOICE:{voice.upper()}] {text}")
        except Exception as exc:
            # Fall back to logging without raising
            print(f"[VOICE ERROR] {exc}")


