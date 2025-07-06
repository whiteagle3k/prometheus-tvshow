import React from 'react'
import ChatFeed from './components/ChatFeed'
import CharacterPanel from './components/CharacterPanel'
import ScenarioPanel from './components/ScenarioPanel'
import StatusPanel from './components/StatusPanel'
import MemoryPanel from './components/MemoryPanel'
import ScenePanel from './components/ScenePanel'
import NarrativePanel from './components/NarrativePanel'
import MoodPanel from './components/MoodPanel'
import { WebSocketProvider } from './components/WebSocketProvider'
import './App.css'

function App() {
  // All state will now come from WebSocketProvider context in child components
  const [selectedCharacter, setSelectedCharacter] = React.useState(null)
  const [activeTab, setActiveTab] = React.useState('chat')

  const handleCharacterSelect = (characterId) => {
    setSelectedCharacter(characterId)
    setActiveTab('memory')
  }

  return (
    <WebSocketProvider>
      <div className="container">
        <div className="header">
          <h1>🎬 AI House Director Console</h1>
          <p>Monitor and control the AI reality show simulation</p>
        </div>
        <div className="main-content">
          <div className="chat-section">
            <div className="chat-header">
              <h2>Live Chat Feed</h2>
            </div>
            <ChatFeed />
          </div>
          <div className="sidebar">
            <div className="sidebar-tabs">
              <button 
                className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
                onClick={() => setActiveTab('chat')}
              >
                Chat
              </button>
              <button 
                className={`tab-btn ${activeTab === 'memory' ? 'active' : ''}`}
                onClick={() => setActiveTab('memory')}
              >
                Memory
              </button>
              <button 
                className={`tab-btn ${activeTab === 'scene' ? 'active' : ''}`}
                onClick={() => setActiveTab('scene')}
              >
                Scene
              </button>
              <button 
                className={`tab-btn ${activeTab === 'narrative' ? 'active' : ''}`}
                onClick={() => setActiveTab('narrative')}
              >
                Story
              </button>
              <button 
                className={`tab-btn ${activeTab === 'mood' ? 'active' : ''}`}
                onClick={() => setActiveTab('mood')}
              >
                Mood
              </button>
            </div>
            <div className="sidebar-content">
              {activeTab === 'chat' && (
                <>
                  <StatusPanel />
                  <CharacterPanel onCharacterSelect={handleCharacterSelect} />
                  <ScenarioPanel />
                </>
              )}
              {activeTab === 'memory' && (
                <MemoryPanel selectedCharacter={selectedCharacter} className="single-panel" />
              )}
              {activeTab === 'scene' && (
                <ScenePanel className="single-panel" />
              )}
              {activeTab === 'narrative' && (
                <NarrativePanel className="single-panel" />
              )}
              {activeTab === 'mood' && (
                <MoodPanel className="single-panel" />
              )}
            </div>
          </div>
        </div>
      </div>
    </WebSocketProvider>
  )
}

export default App 