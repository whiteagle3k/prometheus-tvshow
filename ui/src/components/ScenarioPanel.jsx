import React, { useState } from 'react'
import { useWebSocketData } from './WebSocketProvider'

function ScenarioPanel({ onScenarioTrigger }) {
  const { scenarios = [] } = useWebSocketData()
  const [activating, setActivating] = useState({})
  const [executing, setExecuting] = useState({})

  const activateScenario = async (scenarioId) => {
    setActivating(prev => ({ ...prev, [scenarioId]: true }))
    try {
      const response = await fetch(`/api/tvshow/scenarios/${scenarioId}/activate`, {
        method: 'POST'
      })
      if (response.ok && onScenarioTrigger) {
        onScenarioTrigger()
      }
    } catch (error) {
      // Optionally handle error
    } finally {
      setActivating(prev => ({ ...prev, [scenarioId]: false }))
    }
  }

  const executeScenario = async (scenarioId) => {
    setExecuting(prev => ({ ...prev, [scenarioId]: true }))
    try {
      const response = await fetch(`/api/tvshow/scenarios/${scenarioId}/execute`, {
        method: 'POST'
      })
      if (response.ok && onScenarioTrigger) {
        onScenarioTrigger()
      }
    } catch (error) {
      // Optionally handle error
    } finally {
      setExecuting(prev => ({ ...prev, [scenarioId]: false }))
    }
  }

  if (!scenarios || scenarios.length === 0) {
    return (
      <div className="sidebar-section">
        <h3>Scenarios</h3>
        <div className="loading">Loading scenarios...</div>
      </div>
    )
  }

  return (
    <div className="sidebar-section">
      <h3>Scenarios</h3>
      <ul className="scenario-list">
        {scenarios.map((scenario) => (
          <li key={scenario.scenario_id} className="scenario-item">
            <div className="scenario-name">
              {scenario.title}
            </div>
            <div className="scenario-description">
              {scenario.description}
            </div>
            <div style={{ marginTop: '5px' }}>
              <button
                onClick={() => activateScenario(scenario.scenario_id)}
                disabled={activating[scenario.scenario_id] || scenario.executed}
                className="scenario-trigger"
                style={{
                  marginRight: '5px',
                  opacity: scenario.executed ? 0.5 : 1,
                  cursor: scenario.executed ? 'not-allowed' : 'pointer'
                }}
              >
                {activating[scenario.scenario_id] ? 'Activating...' : 'Activate'}
              </button>
              <button
                onClick={() => executeScenario(scenario.scenario_id)}
                disabled={executing[scenario.scenario_id] || scenario.executed}
                className="scenario-trigger"
                style={{
                  background: scenario.executed ? '#666' : '#45b7aa',
                  opacity: scenario.executed ? 0.5 : 1,
                  cursor: scenario.executed ? 'not-allowed' : 'pointer'
                }}
              >
                {executing[scenario.scenario_id] ? 'Executing...' : scenario.executed ? 'Executed' : 'Execute'}
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default ScenarioPanel 