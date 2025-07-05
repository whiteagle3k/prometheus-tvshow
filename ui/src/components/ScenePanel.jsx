import React, { useState } from 'react'
import { useWebSocketData } from './WebSocketProvider'

function ScenePanel({ className }) {
  const { scene } = useWebSocketData()
  const [activeTab, setActiveTab] = useState('current')

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown'
    const date = new Date(timestamp * 1000)
    return date.toLocaleTimeString()
  }

  const getToneColor = (tone) => {
    const colors = {
      'excited': '#ff6b6b',
      'creative': '#4ecdc4',
      'positive': '#51cf66',
      'curious': '#feca57',
      'calm': '#74c0fc',
      'melancholic': '#868e96',
      'frustrated': '#ff922b',
      'negative': '#ff6b6b',
      'agitated': '#ff922b'
    }
    return colors[tone] || '#888'
  }

  return (
    <div className={`sidebar-section${className ? ' ' + className : ''}`}>
      <h3>Scene Context</h3>
      <div className="tab-buttons">
        <button 
          className={`tab-btn ${activeTab === 'current' ? 'active' : ''}`}
          onClick={() => setActiveTab('current')}
        >
          Current
        </button>
      </div>
      <div className="scene-content">
        {activeTab === 'current' && scene && (
          <div className="current-scene">
            <div className="scene-metrics">
              <div className="metric">
                <span className="metric-label">Theme:</span>
                <span className="metric-value">{scene.theme || 'None'}</span>
              </div>
              <div className="metric">
                <span className="metric-label">Tone:</span>
                <span 
                  className="metric-value" 
                  style={{ color: getToneColor(scene.emotional_tone) }}
                >
                  {scene.emotional_tone || 'Neutral'}
                </span>
              </div>
              <div className="metric">
                <span className="metric-label">Active:</span>
                <span className="metric-value">
                  {scene.active_characters?.join(', ') || 'None'}
                </span>
              </div>
              <div className="metric">
                <span className="metric-label">Triggers:</span>
                <span className="metric-value">
                  {scene.recent_triggers?.join(', ') || 'None'}
                </span>
              </div>
            </div>
            <div className="scene-summary">
              <h4>Scene Summary</h4>
              <p>{scene.summary || 'No summary available'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ScenePanel 