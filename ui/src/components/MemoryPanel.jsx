import React, { useState } from 'react'
import { useWebSocketData } from './WebSocketProvider'

function MemoryPanel({ selectedCharacter, className }) {
  const { memory } = useWebSocketData()
  const [showMemory, setShowMemory] = useState(false)

  const logs = selectedCharacter ? (memory[selectedCharacter] || []) : []

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown'
    const date = new Date(timestamp * 1000)
    return date.toLocaleTimeString()
  }

  const getMessageTypeColor = (type) => {
    const colors = {
      'user': '#4ecdc4',
      'autonomous': '#ff6b6b',
      'response': '#4ecdc4',
      'memory': '#feca57'
    }
    return colors[type] || '#888'
  }

  if (!selectedCharacter) {
    return (
      <div className="sidebar-section">
        <h3>Character Memory</h3>
        <div className="info-text">Select a character to view their memory</div>
      </div>
    )
  }

  // Determine if single-panel stretching should be applied
  const isSinglePanel = className && className.includes('single-panel');

  return (
    <div
      className={`sidebar-section${className ? ' ' + className : ''}`}
      style={isSinglePanel ? { flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' } : undefined}
    >
      <div className="section-header">
        <h3>Memory: {selectedCharacter}</h3>
        <button 
          onClick={() => setShowMemory(!showMemory)}
          className="toggle-btn"
        >
          {showMemory ? 'Hide' : 'Show'} Memory
        </button>
      </div>
      <div className="memory-content">
        {showMemory && (
          <div className="memory-buffer">
            <h4>Recent Memory Buffer</h4>
            <div className="memory-items">
              {logs.slice(-5).map((log, index) => {
                if (!log || typeof log !== 'object' || !('type' in log) || !('timestamp' in log) || !('content' in log)) return null;
                return (
                  <div key={index} className="memory-item">
                    <div className="memory-header">
                      <span className="memory-type" style={{ color: getMessageTypeColor(log.type) }}>
                        {log.type}
                      </span>
                      <span className="memory-timestamp">
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                    <div className="memory-content-text">
                      {typeof log.content === 'object' && log.content !== null
                        ? JSON.stringify(log.content)
                        : log.content}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
        <div className="logs-section">
          <h4>Activity Log</h4>
          <div>
            {logs.map((log, index) => {
              if (!log || typeof log !== 'object' || !('type' in log) || !('timestamp' in log) || !('content' in log)) return null;
              return (
                <div key={index} className="log-item">
                  <div className="log-header">
                    <span className="log-type" style={{ color: getMessageTypeColor(log.type) }}>
                      {log.type}
                    </span>
                    <span className="log-timestamp">
                      {formatTimestamp(log.timestamp)}
                    </span>
                  </div>
                  <div className="log-content">
                    {typeof log.content === 'object' && log.content !== null
                      ? JSON.stringify(log.content)
                      : log.content}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MemoryPanel 