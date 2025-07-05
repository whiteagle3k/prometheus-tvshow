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
          //console.log(data)
          switch (data.type) {
            case 'chat':
              if (data.payload.history) {
                setChat(data.payload.history)
                // Optionally, store the latest timestamp in a ref for smarter deduplication
              } else if (data.payload.message) {
                setChat(prev => {
                  // Only append if this message is newer than the last in the array
                  if (prev.length > 0) {
                    const last = prev[prev.length - 1]
                    if (
                      data.payload.message.timestamp <= last.timestamp &&
                      data.payload.message.character_id === last.character_id &&
                      data.payload.message.content === last.content
                    ) {
                      return prev
                    }
                  }
                  // Also check for any message in the array (for safety)
                  const exists = prev.some(
                    m =>
                      m.timestamp === data.payload.message.timestamp &&
                      m.character_id === data.payload.message.character_id &&
                      m.content === data.payload.message.content
                  )
                  if (exists) return prev
                  return [...prev, data.payload.message].slice(-50)
                })
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