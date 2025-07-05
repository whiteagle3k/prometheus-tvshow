import React, { useState } from 'react'
import { useWebSocketData } from './WebSocketProvider'

function CharacterPanel({ onCharacterInitialized, onCharacterSelect }) {
  const { characters = [], mood = {} } = useWebSocketData()
  const [initializing, setInitializing] = useState({})
  const [showDesc, setShowDesc] = useState({})

  const initializeCharacter = async (characterId) => {
    setInitializing(prev => ({ ...prev, [characterId]: true }))
    try {
      const response = await fetch(`/api/tvshow/characters/${characterId}/init`, {
        method: 'POST'
      })
      if (response.ok && typeof onCharacterInitialized === 'function') {
        onCharacterInitialized()
      }
    } catch (error) {
      // Optionally handle error
    } finally {
      setTimeout(() => setInitializing(prev => ({ ...prev, [characterId]: false })), 800)
    }
  }

  const getMoodEmoji = (mood) => {
    const emojis = {
      'joy': '😊',
      'excitement': '🤩',
      'curiosity': '🤔',
      'calm': '😌',
      'melancholy': '😔',
      'frustration': '😤',
      'anger': '😠',
      'anxiety': '😰',
      'neutral': '😐'
    }
    return emojis[mood] || '😐'
  }

  if (!characters || characters.length === 0) {
    return (
      <div className="sidebar-section">
        <h3>Characters</h3>
        <div className="loading">Loading characters...</div>
      </div>
    )
  }

  return (
    <div className="sidebar-section">
      <h3>Characters</h3>
      <ul className="character-list">
        {characters.map((character) => {
          const isRunning = character.status === 'running' || character.initialized
          const moodData = mood[character.id]
          const moodEmoji = moodData ? getMoodEmoji(moodData.primary_mood) : '😐'
          return (
            <li key={character.id} className="character-item">
              <div className="character-info">
                <span 
                  className="info-icon"
                  title="Show description"
                  onClick={() => setShowDesc(prev => ({...prev, [character.id]: !prev[character.id]}))}
                >
                  <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor">
                    <circle cx="10" cy="10" r="9" stroke="#4ecdc4" strokeWidth="2" fill="none"/>
                    <text x="10" y="15" textAnchor="middle" fontSize="12" fill="#4ecdc4">i</text>
                  </svg>
                </span>
                <span className="character-name">{character.name}</span>
                <span className="mood-indicator" title={moodData?.primary_mood || 'neutral'}>
                  {moodEmoji}
                </span>
              </div>
              <div className="character-controls">
                <button
                  onClick={() => initializeCharacter(character.id)}
                  disabled={isRunning || initializing[character.id]}
                  className={`init-btn ${isRunning ? 'running' : ''} ${initializing[character.id] ? 'initializing' : ''}`}
                >
                  {isRunning ? 'Running' : initializing[character.id] ? 'Initializing...' : 'Initialize'}
                </button>
                {isRunning && (
                  <button
                    onClick={() => onCharacterSelect && onCharacterSelect(character.id)}
                    className="memory-btn"
                    title="View Memory"
                  >
                    🧠
                  </button>
                )}
              </div>
              {showDesc[character.id] && (
                <div className="character-description">
                  {character.description}
                </div>
              )}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default CharacterPanel 