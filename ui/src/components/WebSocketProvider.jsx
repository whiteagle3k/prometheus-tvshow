import React, { createContext, useContext, useEffect, useRef, useState } from 'react'

const WebSocketContext = createContext(null)

export function useWebSocketData() {
  return useContext(WebSocketContext)
}

export function WebSocketProvider({ children }) {
  const [chat, setChat] = useState([])
  const [mood, setMood] = useState({})
  const [memory, setMemory] = useState({})
  const [scene, setScene] = useState(null)
  const [narrative, setNarrative] = useState([])
  const wsRef = useRef(null)
  const reconnectTimeout = useRef(null)

  useEffect(() => {
    let ws
    let reconnectAttempts = 0
    function connect() {
      ws = new window.WebSocket(`ws://${window.location.host}/tvshow/ws`)
      wsRef.current = ws
      ws.onopen = () => {
        reconnectAttempts = 0
      }
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          switch (data.type) {
            case 'chat':
              if (data.payload.history) {
                setChat(data.payload.history)
              } else if (data.payload.message) {
                setChat(prev => [...prev, data.payload.message].slice(-50))
              }
              break
            case 'mood':
              setMood(prev => ({ ...prev, ...data.payload }))
              break
            case 'memory':
              setMemory(prev => ({ ...prev, [data.payload.character_id]: data.payload.log }))
              break
            case 'scene':
              setScene(data.payload)
              break
            case 'narrative':
              setNarrative(data.payload)
              break
            default:
              break
          }
        } catch (e) {
          // Ignore parse errors
        }
      }
      ws.onclose = () => {
        if (reconnectAttempts < 10) {
          reconnectTimeout.current = setTimeout(connect, 1000 * (reconnectAttempts + 1))
          reconnectAttempts++
        }
      }
      ws.onerror = () => {
        ws.close()
      }
    }
    connect()
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current)
    }
  }, [])

  const value = {
    chat,
    mood,
    memory,
    scene,
    narrative
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
} 