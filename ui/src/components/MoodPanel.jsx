import React, { useState } from 'react'
import { useWebSocketData } from './WebSocketProvider'

function MoodPanel({ className }) {
  const { mood } = useWebSocketData()
  const [selectedCharacter, setSelectedCharacter] = useState(null)
  const [moodFeedback, setMoodFeedback] = useState('')

  const applyMoodFeedback = async (characterId, feedback) => {
    try {
      await fetch(`/api/tvshow/characters/${characterId}/mood/feedback`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ feedback })
      })
      setMoodFeedback('')
    } catch (error) {
      // Optionally handle error
    }
  }

  const getMoodColor = (moodVal) => {
    const colors = {
      'joy': '#51cf66',
      'excitement': '#ff6b6b',
      'curiosity': '#feca57',
      'calm': '#74c0fc',
      'melancholy': '#868e96',
      'frustration': '#ff922b',
      'anger': '#ff6b6b',
      'anxiety': '#ff922b',
      'neutral': '#888'
    }
    return colors[moodVal] || '#888'
  }

  const getMoodEmoji = (moodVal) => {
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
    return emojis[moodVal] || '😐'
  }

  return (
    <div className={`sidebar-section${className ? ' ' + className : ''}`}>
      <h3>Emotional States</h3>
      <div className="mood-content">
        <div className="moods-overview">
          <h4>Character Moods</h4>
          {Object.entries(mood).map(([characterId, moodVal]) => (
            <div key={characterId} className="mood-item">
              <div className="mood-header">
                <span className="character-name">{characterId}</span>
                <span className="mood-emoji" title={moodVal}>{getMoodEmoji(moodVal)}</span>
              </div>
              <div className="mood-details">
                <div className="mood-primary">
                  <span className="mood-label">Primary:</span>
                  <span className="mood-value" style={{ color: getMoodColor(moodVal) }}>{moodVal}</span>
                </div>
              </div>
              <button onClick={() => setSelectedCharacter(characterId)} className="mood-detail-btn">Details</button>
            </div>
          ))}
        </div>
        {selectedCharacter && mood[selectedCharacter] && (
          <div className="mood-details-panel">
            <div className="details-header">
              <h4>{selectedCharacter} - Mood Details</h4>
              <button onClick={() => setSelectedCharacter(null)} className="close-btn">×</button>
            </div>
            <div className="mood-feedback">
              <h5>Apply Emotional Feedback</h5>
              <div className="feedback-input">
                <input
                  type="text"
                  value={moodFeedback}
                  onChange={(e) => setMoodFeedback(e.target.value)}
                  placeholder="Enter mood event (e.g., success, failure, stress)"
                  className="feedback-field"
                />
                <button 
                  onClick={() => applyMoodFeedback(selectedCharacter, moodFeedback)}
                  disabled={!moodFeedback.trim()}
                  className="feedback-btn"
                >
                  Apply
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default MoodPanel 