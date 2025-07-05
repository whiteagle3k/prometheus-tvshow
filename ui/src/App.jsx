import React, { useState, useEffect } from 'react'
import ChatFeed from './components/ChatFeed'
import CharacterPanel from './components/CharacterPanel'
import ScenarioPanel from './components/ScenarioPanel'
import StatusPanel from './components/StatusPanel'
import './App.css'

function App() {
  const [status, setStatus] = useState(null)
  const [characters, setCharacters] = useState([])
  const [scenarios, setScenarios] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch initial data
  useEffect(() => {
    fetchInitialData()
  }, [])

  const fetchInitialData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch status
      const statusResponse = await fetch('/api/tvshow/status')
      if (statusResponse.ok) {
        const statusData = await statusResponse.json()
        setStatus(statusData)
      }

      // Fetch characters
      const charactersResponse = await fetch('/api/tvshow/characters')
      if (charactersResponse.ok) {
        const charactersData = await charactersResponse.json()
        setCharacters(charactersData.characters || [])
      }

      // Fetch scenarios
      const scenariosResponse = await fetch('/api/tvshow/scenarios')
      if (scenariosResponse.ok) {
        const scenariosData = await scenariosResponse.json()
        setScenarios(scenariosData.scenarios || [])
      }

    } catch (err) {
      setError('Failed to load initial data: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchCharacters = async () => {
    try {
      const charactersResponse = await fetch('/api/tvshow/characters')
      if (charactersResponse.ok) {
        const charactersData = await charactersResponse.json()
        setCharacters(charactersData.characters || [])
      }
    } catch (err) {
      // Optionally handle error
    }
  }

  const refreshData = () => {
    fetchInitialData()
  }

  if (loading) {
    return (
      <div className="container">
        <div className="loading">Loading TV Show Director Console...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container">
        <div className="error">{error}</div>
        <button onClick={refreshData}>Retry</button>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <h1>🎬 TV Show Director Console</h1>
        <p>Monitor and control the AI reality show simulation</p>
      </div>

      <div className="main-content">
        <div className="chat-section">
          <div className="chat-header">
            <h2>Live Chat Feed</h2>
            <button onClick={refreshData}>Refresh</button>
          </div>
          <ChatFeed />
        </div>

        <div className="sidebar">
          <StatusPanel status={status} />
          <CharacterPanel characters={characters} onCharacterInitialized={fetchCharacters} />
          <ScenarioPanel scenarios={scenarios} onScenarioTrigger={refreshData} />
        </div>
      </div>
    </div>
  )
}

export default App 