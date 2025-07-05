import React from 'react'
import { useWebSocketData } from './WebSocketProvider'

function StatusPanel() {
  const { status } = useWebSocketData()
  if (!status) {
    return (
      <div className="sidebar-section">
        <h3>System Status</h3>
        <div className="loading">Loading status...</div>
      </div>
    )
  }
  return (
    <div className="sidebar-section">
      <h3>System Status</h3>
      <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
        <div>
          <strong>Status:</strong> {status.status}
        </div>
        <div>
          <strong>Characters:</strong> {status.characters_initialized}/{status.total_characters}
        </div>
        <div>
          <strong>Active Scenarios:</strong> {status.active_scenarios}
        </div>
        <div>
          <strong>Total Messages:</strong> {status.total_messages}
        </div>
        <div>
          <strong>Scenarios Executed:</strong> {status.scenarios_executed}
        </div>
      </div>
    </div>
  )
}

export default StatusPanel 