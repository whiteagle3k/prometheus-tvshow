# TV Show UI

React-based director console for the TV Show Extension.

## Features

- **Live Chat Feed**: Real-time display of character messages
- **Character Management**: Initialize and monitor AI characters
- **Scenario Control**: Activate and execute narrative scenarios
- **System Status**: Monitor overall show status and metrics
- **Message Injection**: Send messages as any character

## Development

### Prerequisites

- Node.js 16+ and npm
- Backend server running on port 8000

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Development Server

The development server runs on `http://localhost:3001` and proxies API requests to the backend at `http://localhost:8000`.

### Production Build

The production build is created in the `dist/` directory and served by the backend at `/tvshow/ui/`.

## Architecture

### Components

- **App.jsx**: Main application component
- **ChatFeed.jsx**: Live chat display and message input
- **StatusPanel.jsx**: System status and metrics
- **CharacterPanel.jsx**: Character management and initialization
- **ScenarioPanel.jsx**: Scenario activation and execution

### API Integration

The UI connects to the backend API endpoints:

- `GET /api/tvshow/status` - System status
- `GET /api/tvshow/characters` - Available characters
- `POST /api/tvshow/characters/{id}/init` - Initialize character
- `GET /api/tvshow/scenarios` - Available scenarios
- `POST /api/tvshow/scenarios/{id}/activate` - Activate scenario
- `POST /api/tvshow/scenarios/{id}/execute` - Execute scenario
- `GET /api/tvshow/chat/history` - Chat history
- `POST /api/tvshow/chat` - Send message

### Styling

The UI uses a dark theme with:
- Background: `#1a1a1a`
- Cards: `#2a2a2a`
- Text: `#ffffff`
- Accent: `#ff6b6b` (red)
- Secondary: `#4ecdc4` (teal)

## Usage

1. Start the backend server
2. Access the UI at `http://localhost:8000/tvshow`
3. Initialize characters using the sidebar
4. Activate scenarios to trigger narrative events
5. Send messages as characters using the chat input
6. Monitor the live chat feed for character interactions

## Future Enhancements

- WebSocket support for real-time updates
- Character mood indicators
- Advanced scenario editing
- Chat filtering and search
- Character relationship visualization 