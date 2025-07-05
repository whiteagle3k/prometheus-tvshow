import React, { useState } from 'react'

function CharacterPanel({ characters }) {
  const [initializing, setInitializing] = useState({})

  const initializeCharacter = async (characterId) => {
    setInitializing(prev => ({ ...prev, [characterId]: true }))
    
    try {
      const response = await fetch(`/api/tvshow/characters/${characterId}/init`, {
        method: 'POST'
      })
      
      if (response.ok) {
        // Could trigger a refresh of the parent component
        console.log(`Character ${characterId} initialized`)
      } else {
        console.error(`Failed to initialize character ${characterId}`)
      }
    } catch (error) {
      console.error(`Error initializing character ${characterId}:`, error)
    } finally {
      setInitializing(prev => ({ ...prev, [characterId]: false }))
    }
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
        {characters.map((character) => (
          <li key={character.id} className="character-item">
            <div className="character-name-small">
              {character.name}
            </div>
            <div className="character-description">
              {character.description}
            </div>
            <button
              onClick={() => initializeCharacter(character.id)}
              disabled={initializing[character.id]}
              style={{
                background: '#ff6b6b',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                padding: '4px 8px',
                fontSize: '11px',
                cursor: initializing[character.id] ? 'not-allowed' : 'pointer',
                marginTop: '5px',
                opacity: initializing[character.id] ? 0.6 : 1
              }}
            >
              {initializing[character.id] ? 'Initializing...' : 'Initialize'}
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default CharacterPanel 