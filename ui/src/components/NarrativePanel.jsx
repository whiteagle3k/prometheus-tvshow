import React from 'react'
import { useWebSocketData } from './WebSocketProvider'

function NarrativePanel() {
  const { narrative } = useWebSocketData()

  const getPhaseColor = (phase) => {
    const colors = {
      'intro': '#4ecdc4',
      'conflict': '#ff6b6b',
      'resolution': '#51cf66',
      'climax': '#ff922b',
      'falling_action': '#868e96'
    }
    return colors[phase] || '#888'
  }

  const getArcStatusColor = (status) => {
    const colors = {
      'active': '#51cf66',
      'inactive': '#868e96',
      'completed': '#4ecdc4',
      'paused': '#ff922b'
    }
    return colors[status] || '#888'
  }

  return (
    <div className="sidebar-section">
      <h3>Narrative Arcs</h3>
      <div className="narrative-content">
        <div className="available-arcs">
          <h4>Storylines</h4>
          {narrative.map(arc => (
            <div key={arc.arc_id} className={`arc-item ${arc.status}`}>
              <div className="arc-header">
                <span className="arc-title">{arc.title}</span>
                <span 
                  className="arc-status"
                  style={{ color: getArcStatusColor(arc.status) }}
                >
                  {arc.status}
                </span>
              </div>
              <div className="arc-description">{arc.description}</div>
              <div className="arc-phase">
                <span className="phase-label">Phase:</span>
                <span 
                  className="phase-value"
                  style={{ color: getPhaseColor(arc.current_phase) }}
                >
                  {arc.current_phase || 'Unknown'}
                </span>
              </div>
              <div className="arc-progress">
                <span className="progress-label">Progress:</span>
                <span className="progress-value">
                  {arc.progress || 0}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default NarrativePanel 