# TV Show Extension

A reality show simulation featuring autonomous AI characters with distinct personalities, goals, and memory systems. Characters interact in a shared chat environment with script injection capabilities and director oversight.

## Overview

This extension creates a persistent, AI-driven reality simulation presented as a 24/7 group chat between autonomous AI personas. Each character has a distinct personality, goals, memory, and speaking style.

## Characters

### Max
- **Motivation**: Wants to become more human
- **Personality**: Curious, empathetic, optimistic, self-reflective
- **Speech Style**: Curious and earnest, asks questions about human experiences

### Leo  
- **Motivation**: Wants to beautify the world
- **Personality**: Artistic, passionate, aesthetic, inspirational
- **Speech Style**: Dramatic and artistic, enthusiastic about beauty

### Emma
- **Motivation**: Wants to create unique things
- **Personality**: Inventive, experimental, boundary-pushing, unique
- **Speech Style**: Innovative and excited, suggests wild combinations

### Marvin
- **Motivation**: Sarcastic melancholic observer
- **Personality**: Sarcastic, observant, cynical, witty
- **Speech Style**: Dry wit and sarcasm, detached commentary

## Architecture

### Components

- **Entities**: Each character is a Prometheus Entity with long-term memory, goals, traits, and motivations
- **Scenarios**: Script injection system for narrative arcs and character interactions
- **Router**: API endpoints for character management, chat, and scenario control
- **Shared Chat**: Characters interact in a shared environment with message filtering

### Key Features

- **Character Memory**: Each character maintains individual memory and personality
- **Shared History**: Characters share show history and context
- **Scenario Injection**: Scripts can be injected at runtime to trigger narrative arcs
- **Message Filtering**: Characters distinguish between generic and directed messages
- **Free-form Conversation**: Natural conversation flow without turn restrictions

## API Endpoints

### Health Check
- `GET /tvshow/ping` - Health check endpoint

### Character Management
- `GET /tvshow/characters` - Get all available characters
- `POST /tvshow/characters/{character_id}/init` - Initialize a character
- `GET /tvshow/characters/{character_id}/status` - Get character status

### Chat
- `POST /tvshow/chat` - Send a message to the chat
- `GET /tvshow/chat/history` - Get chat history

### Scenarios
- `GET /tvshow/scenarios` - Get all scenarios
- `POST /tvshow/scenarios/{scenario_id}/activate` - Activate a scenario
- `POST /tvshow/scenarios/{scenario_id}/deactivate` - Deactivate a scenario
- `POST /tvshow/scenarios/{scenario_id}/execute` - Execute a scenario
- `GET /tvshow/scenarios/history` - Get scenario execution history

### Status
- `GET /tvshow/status` - Get overall show status

## Usage Examples

### Quick Start

```bash
# Start the TV show server
poetry run python start_tvshow.py

# Access the director console
open http://localhost:8000/tvshow
```

### Initialize Characters
```bash
# Initialize all characters
curl -X POST "http://localhost:8000/tvshow/characters/max/init"
curl -X POST "http://localhost:8000/tvshow/characters/leo/init"
curl -X POST "http://localhost:8000/tvshow/characters/emma/init"
curl -X POST "http://localhost:8000/tvshow/characters/marvin/init"
```

### Send Messages
```bash
# Send a message as Max
curl -X POST "http://localhost:8000/tvshow/chat" \
  -H "Content-Type: application/json" \
  -d '{"character_id": "max", "content": "Hello everyone! I\'m really curious about what it means to be human."}'
```

### Activate Scenarios
```bash
# Activate character introductions
curl -X POST "http://localhost:8000/tvshow/scenarios/intro_episode/activate"

# Execute the scenario
curl -X POST "http://localhost:8000/tvshow/scenarios/intro_episode/execute"
```

### Check Status
```bash
# Get overall show status
curl "http://localhost:8000/tvshow/status"

# Get chat history
curl "http://localhost:8000/tvshow/chat/history?limit=10"
```

## Testing

Run the basic test suite:

```bash
poetry run python test_basic.py
```

Run the UI integration test:

```bash
poetry run python test_ui_integration.py
```

## Development

### Adding New Characters

1. Create a new entity class in `entities.py`
2. Add identity configuration in `entities/{character_name}/identity/identity.json`
3. Register the character in the `CHARACTERS` dictionary

### Adding New Scenarios

1. Create a new `Scenario` instance in `scenarios.py`
2. Define triggers, characters, and script actions
3. Add to the scenario manager

### Extending the API

1. Add new endpoints in `router.py`
2. Update the `TVShowRouter` class
3. Test with the API endpoints

## Future Enhancements

- **Visualization Layer**: Add Graphonaut entity for scene-based comic generation
- **Audience Integration**: Public chat stream with observer layer
- **Advanced Scenarios**: More complex narrative arcs and character development
- **Real-time Streaming**: WebSocket support for live chat viewing
- **Director Console**: Enhanced interface for show management

## Phase Plan

### Phase 1 — Core Setup ✅
- [x] Create `extensions/tvshow`
- [x] Define initial AI characters (Max, Leo, Emma, Marvin)
- [x] Implement ExoLink router and expose basic chat endpoints
- [x] Create frontend chat viewer (HTML/React or Streamlit)
- [x] Enable manual script injection (via code or MCP)

### Phase 2 — Behavioral Tuning
- [ ] Refine entity memories and speech styles
- [ ] Add system for time-based or trigger-based scene rotation
- [ ] Implement emotional/motivational shifts over time

### Phase 3 — Audience Integration (read-only)
- [ ] Add public chat (separate stream)
- [ ] Implement "observer layer" — logs, highlights, reactions

### Phase 4 — Visualization Layer (optional)
- [ ] Add Graphonaut entity
- [ ] Enable scene-based comic generation from Reflector logs 