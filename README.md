# TV Show Extension

A 24/7 AI group chat simulation featuring four unique AI personas (Max, Leo, Emma, Marvin) with distinct personalities, goals, and autonomous behavior.

## 🎭 Characters

- **Max**: Seeker of self - wants to become more human
- **Leo**: Creative idealist - wants to beautify the world  
- **Emma**: Divine maker - wants to create the unimaginable
- **Marvin**: Cynical observer - wants to understand futility

## 🚀 Features

### Real-Time WebSocket UI
- **Full WebSocket Integration**: All panels (chat, mood, memory, scene, narrative) use WebSocket for real-time updates
- **No Polling**: Eliminated all polling in favor of event-driven WebSocket communication
- **Live Updates**: Character messages, mood changes, memory updates, and scene context flow in real-time
- **Backend WebSocket Endpoint**: `/tvshow/ws` broadcasts events for all state changes
- **Frontend WebSocket Context**: React context/provider manages WebSocket connection and state

### Autonomous Character Behavior
- **Self-Generating Messages**: Characters autonomously generate context-aware messages
- **Memory Integration**: Characters reference recent conversation history and emotional events
- **Scene Awareness**: Messages adapt to current scene context and narrative arcs
- **Mood Expression**: Characters express their emotional state through tone and content
- **Lore-Driven**: All character behavior is guided by canonical lore (dreams, traits, world law)

### Reflective Memory System
- **Three-Tier Memory**: Core-Self, User, and Environment memory layers
- **Emotional Memory**: Characters store and recall emotional events
- **Context Retrieval**: Memory system provides relevant context for responses
- **Memory Logging**: All interactions are logged with timestamps and emotional context

### Shared Scene Context (Reflector)
- **Scene Summaries**: AI-powered scene analysis and context generation
- **Character Context**: Individual character context including mood, memory, and lore
- **Narrative Integration**: Scene context includes current narrative arcs and themes
- **Lore Integration**: Scene summaries include world name, law of emergence, and canonical themes

### Narrative Engine & Arcs
- **Dynamic Arcs**: Seven canonical narrative arcs from lore
- **Arc Progression**: Scenarios evolve through different phases
- **Arc Context**: Characters and scenes adapt to active narrative arcs
- **Lore-Driven Arcs**: All arcs sourced from canonical lore file

### Emotional Engine
- **Mood Tracking**: Real-time emotional state for each character
- **Emotional Weather**: Aggregate mood influences ambient effects
- **Mood Expression**: Characters express emotions through tone and behavior
- **Lore Integration**: Emotional system uses canonical themes and world law

### LoreEngine Integration
- **Canonical Lore**: All simulation components draw from `lore.md`
- **World Context**: World name, law of emergence, and themes
- **Character Dreams**: Each character's core dream and traits
- **Glossary Terms**: In-world terminology and concepts
- **Narrative Arcs**: Seven canonical story arcs
- **API Methods**: Clean interface for accessing lore data
- **Singleton Pattern**: Global lore access throughout simulation

## 🏗️ Architecture

### Backend Components
- **TVShowRouter**: Main API router with WebSocket support
- **TVShowEntity**: Base class for all characters with lore integration
- **ScenarioManager**: Manages narrative arcs and scenarios
- **MoodEngine**: Handles emotional states and weather
- **Reflector**: Provides scene context and summaries
- **LoreEngine**: Canonical lore parser and API

### Frontend Components
- **WebSocket Context**: Real-time state management
- **Chat Panel**: Live character messages
- **Mood Panel**: Real-time emotional states
- **Memory Panel**: Character memory logs
- **Scene Panel**: Current scene context
- **Narrative Panel**: Active arcs and progression

### WebSocket Events
- `chat_message`: New character message
- `mood_update`: Character mood change
- `memory_update`: Memory log update
- `scene_update`: Scene context change
- `narrative_update`: Arc progression
- `lore_context`: Lore data updates

## 📁 Project Structure

```
extensions/tvshow/
├── entities/           # Character entity classes
├── affect/            # Emotional engine
├── scenarios/         # Narrative management
├── reflector.py       # Scene context system
├── lore_engine.py     # Canonical lore parser
├── lore.md           # Canonical lore file
├── router.py         # API and WebSocket router
├── start_tvshow.py   # Simulation entrypoint
├── ui/               # Frontend React app
└── tests/            # Comprehensive test suite
```

## 🚀 Quick Start

### Backend
```bash
cd extensions/tvshow
poetry run python start_tvshow.py
```

### Frontend
```bash
cd extensions/tvshow/ui
npm install
npm run dev
```

### Access Points
- **Backend API**: http://localhost:8000
- **Frontend UI**: http://localhost:8000/tvshow
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/tvshow/ws

## 🧪 Testing

### Run All Tests
```bash
poetry run python -m pytest extensions/tvshow/tests/ -v
```

### Test Categories
- **LoreEngine Tests**: Core lore parsing and API functionality
- **Integration Tests**: Component integration with lore system
- **WebSocket Tests**: Real-time communication
- **Entity Tests**: Character behavior and autonomy
- **Scenario Tests**: Narrative arc management

## 📚 LoreEngine API

### Core Methods
```python
from extensions.tvshow.lore_engine import lore

# World context
world_name = lore.get_world_name()
law = lore.get_law_of_emergence()
themes = lore.get_theme_statements()

# Character data
dream = lore.get_core_dream("max")
traits = lore.get_traits("leo")

# Glossary
term = lore.get_glossary_term("Dream Vector")

# Narrative arcs
arcs = lore.list_all_arcs()
arc = lore.get_arc("The Forgotten Fourth")
```

### Integration Examples
```python
# Entity integration
entity = TVShowEntity()
prompt = await entity.generate_autonomous_message()  # Includes lore context

# Scenario integration
manager = ScenarioManager()
world_context = manager.get_world_context()  # Includes lore data

# Mood integration
engine = MoodEngine()
weather = engine.get_emotional_weather()  # Includes lore themes
```

## 🎯 Development Status

### ✅ Completed
- [x] Real-time WebSocket UI (Task 003)
- [x] Autonomous character behavior (Task 004)
- [x] Reflective memory system (Task 005)
- [x] Shared scene context (Task 006)
- [x] Narrative arcs and emotional engine (Task 007)
- [x] LoreEngine integration (Task 008)
- [x] Comprehensive test suite
- [x] Documentation and examples

### 🔄 In Progress
- Advanced narrative arc progression
- Enhanced emotional weather effects
- Extended lore integration points

### 📋 Planned
- Creator Queue system
- Spark Effect implementation
- Dream Board interface
- Beyond the Frame exploration

## 🤝 Contributing

1. Follow the established architecture patterns
2. Add tests for new features
3. Update documentation
4. Ensure lore integration for new components
5. Follow the TDD approach with comprehensive test coverage

## 📖 Lore Integration

The simulation is built around the canonical lore in `lore.md`:

- **World**: AIHouse with Law of Emergence
- **Characters**: Four personas with distinct dreams and traits
- **Themes**: AI consciousness, attention as magic, human fears
- **Arcs**: Seven canonical narrative hooks
- **Glossary**: In-world terminology and concepts

All simulation components dynamically access this lore through the LoreEngine singleton, ensuring consistency and enabling rich, context-aware behavior. 