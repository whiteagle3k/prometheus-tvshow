import React, { useState } from 'react'

function CharacterPanel({ characters, onCharacterInitialized }) {
  const [initializing, setInitializing] = useState({})
  const [showDesc, setShowDesc] = useState({})

  // Debug: log characters array
  console.log('CharacterPanel characters:', characters)

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
          return (
            <li key={character.id} className="character-item" style={{display:'flex', alignItems:'center', gap:8, padding:'8px 0'}}>
              <span 
                style={{cursor: 'pointer', color: '#4ecdc4', display:'flex', alignItems:'center'}}
                title="Show description"
                onClick={() => setShowDesc(prev => ({...prev, [character.id]: !prev[character.id]}))}
              >
                <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" style={{marginRight:4}}><circle cx="10" cy="10" r="9" stroke="#4ecdc4" strokeWidth="2" fill="none"/><text x="10" y="15" textAnchor="middle" fontSize="12" fill="#4ecdc4">i</text></svg>
              </span>
              <span className="character-name-small" style={{color:'#fff', fontWeight:'bold', marginRight:8}}>{character.name}</span>
              <button
                onClick={() => initializeCharacter(character.id)}
                disabled={isRunning || initializing[character.id]}
                style={{
                  background: isRunning ? '#333' : initializing[character.id] ? '#888' : '#444',
                  color: isRunning ? 'green' : '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '2px 10px',
                  fontSize: '11px',
                  cursor: isRunning ? 'default' : initializing[character.id] ? 'not-allowed' : 'pointer',
                  marginLeft: 8,
                  opacity: initializing[character.id] ? 0.7 : 1,
                  minWidth: 70
                }}
              >
                {isRunning ? 'Running' : initializing[character.id] ? 'Initializing...' : 'Initialize'}
              </button>
              {showDesc[character.id] && (
                <div className="character-description" style={{background:'#222', color:'#ccc', borderRadius:4, padding:'6px 10px', marginLeft:12, zIndex:2, position:'absolute', marginTop:32, minWidth:180}}>
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