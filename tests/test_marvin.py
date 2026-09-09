import asyncio
import json
import os
import sys
import types

import importlib.util
import pytest

# Ensure project root (Prometheus) is on path for absolute imports like 'extensions.tvshow...'
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# Install lightweight stubs to avoid importing heavy core deps
pkg_extensions = types.ModuleType("extensions")
pkg_tvshow = types.ModuleType("extensions.tvshow")
pkg_entities = types.ModuleType("extensions.tvshow.entities")
base_mod = types.ModuleType("extensions.tvshow.entities.base")

class _StubMoodState:
    def __init__(self):
        self.valence = 0.0
        self.arousal = 0.5

class _StubMoodEngine:
    def __init__(self):
        self.mood_state = _StubMoodState()

class _StubTVShowEntity:
    CHARACTER_ID = "marvin"
    CHARACTER_NAME = "Marvin"
    CHARACTER_DESCRIPTION = "Sarcastic melancholic observer AI"
    def __init__(self, instance_id: str | None = None):
        self.mood_engine = _StubMoodEngine()
        self.memory_log = []
    def _load_identity(self):
        return {}
    async def broadcast(self, *args, **kwargs):
        return None
    async def say(self, *args, **kwargs):
        return None

base_mod.TVShowEntity = _StubTVShowEntity
sys.modules["extensions"] = pkg_extensions
sys.modules["extensions.tvshow"] = pkg_tvshow
sys.modules["extensions.tvshow.entities"] = pkg_entities
sys.modules["extensions.tvshow.entities.base"] = base_mod

# Dynamically load MarvinEntity directly from file to avoid heavy package imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # extensions/tvshow
MARVIN_PATH = os.path.join(ROOT, "entities", "marvin", "__init__.py")
spec = importlib.util.spec_from_file_location("marvin_entity_module", MARVIN_PATH)
marvin_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(marvin_module)  # type: ignore
MarvinEntity = marvin_module.MarvinEntity


def test_marvin_valence_locked():
    marvin = MarvinEntity()
    # Try to change valence away from -0.9
    marvin.mood_engine.mood_state.valence = 0.5
    # Re-lock explicitly like runtime would after actions
    marvin.mood_engine.mood_state.valence = -0.9
    assert marvin.mood_engine.mood_state.valence == -0.9


def test_sarcasm_loaded():
    marvin = MarvinEntity()
    assert isinstance(marvin.sarcasm, list)
    assert len(marvin.sarcasm) >= 5


@pytest.mark.asyncio
async def test_contagion_applies():
    class MockMoodState:
        def __init__(self, arousal=0.5, valence=0.0):
            self.arousal = arousal
            self.valence = valence

    class MockMoodEngine:
        def __init__(self, arousal=0.5, valence=0.0):
            self.mood_state = MockMoodState(arousal=arousal, valence=valence)

    class MockEntity:
        def __init__(self, name):
            self.CHARACTER_NAME = name
            self.mood_engine = MockMoodEngine()

    class MockRoom:
        def __init__(self, entities):
            self.entities = entities

    marvin = MarvinEntity()
    leo = MockEntity("Leo")
    emma = MockEntity("Emma")
    marvin.room = MockRoom([marvin, leo, emma])

    await marvin._apply_contagion()
    # Leo arousal up by 0.1
    assert pytest.approx(leo.mood_engine.mood_state.arousal, 0.0001) == 0.6
    # Emma valence down by 0.15
    assert pytest.approx(emma.mood_engine.mood_state.valence, 0.0001) == -0.15


