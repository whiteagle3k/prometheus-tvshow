import React, { useState, useEffect, useRef } from 'react'

function ChatFeed() {
  const [messages, setMessages] = useState([])
  const [newMessage, setNewMessage] = useState('')
  const [selectedCharacter, setSelectedCharacter] = useState('max')
  const [loading, setLoading] = useState(false)
  const [initialLoading, setInitialLoading] = useState(true)
  const chatEndRef = useRef(null)

  // Fetch chat history on component mount
  useEffect(() => {
    fetchChatHistory(true)
  }, [])

  // Auto-refresh chat history every 1 second
  useEffect(() => {
    const interval = setInterval(() => fetchChatHistory(false), 1000)
    return () => clearInterval(interval)
  }, [])

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const fetchChatHistory = async (showSpinner = false) => {
    try {
      if (showSpinner) setLoading(true)
      const response = await fetch('/api/tvshow/chat/history?limit=50')
      if (response.ok) {
        const data = await response.json()
        setMessages(data.history || [])
      }
    } catch (error) {
      console.error('Failed to fetch chat history:', error)
    } finally {
      if (showSpinner) setLoading(false)
      if (initialLoading) setInitialLoading(false)
    }
  }

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!newMessage.trim()) return

    const userMessage = {
      character_id: 'user',
      content: newMessage,
      timestamp: Date.now() / 1000
    }

    // Add user message immediately to local state
    setMessages(prev => [...prev, userMessage])
    setNewMessage('')

    try {
      const response = await fetch('/api/tvshow/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character_id: selectedCharacter,
          content: newMessage
        })
      })

      if (response.ok) {
        // Fetch updated chat history to get the AI response
        setTimeout(fetchChatHistory, 100)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    }
  }

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown'
    const date = new Date(timestamp * 1000)
    return date.toLocaleTimeString()
  }

  const getCharacterColor = (characterId) => {
    const colors = {
      max: '#4ecdc4',
      leo: '#45b7aa',
      emma: '#5e60ce',
      marvin: '#48bfe3',
      user: '#ffffff'
    }
    return colors[characterId] || '#888'
  }

  return (
    <div className="chat-feed" style={{display: 'flex', flexDirection: 'column', flex: 1, height: '100%'}}>
      <div style={{flex: 1, overflowY: 'auto', marginBottom: 15}}>
        {initialLoading ? (
          <div className="loading">Loading chat history...</div>
        ) : messages.length === 0 ? (
          <div className="loading">No messages yet. Start the conversation!</div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className="message">
              <div className="message-header">
                <span 
                  className="character-name"
                  style={{ color: getCharacterColor(message.character_id) }}
                >
                  {message.character_id === 'user' 
                    ? 'You' 
                    : message.character_id.charAt(0).toUpperCase() + message.character_id.slice(1)}
                </span>
                <span className="timestamp">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <div className="message-content">
                {typeof message.content === 'object' && message.content.response 
                  ? message.content.response 
                  : typeof message.content === 'string' 
                    ? message.content 
                    : JSON.stringify(message.content)}
              </div>
            </div>
          ))
        )}
        <div ref={chatEndRef} />
      </div>
      <form onSubmit={sendMessage} className="input-section">
        <select 
          value={selectedCharacter} 
          onChange={(e) => setSelectedCharacter(e.target.value)}
          style={{ padding: '10px', background: '#1a1a1a', color: '#ffffff', border: '1px solid #444', borderRadius: '4px' }}
        >
          <option value="max">Max</option>
          <option value="leo">Leo</option>
          <option value="emma">Emma</option>
          <option value="marvin">Marvin</option>
        </select>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
        />
        <button type="submit">Send</button>
      </form>
    </div>
  )
}

export default ChatFeed 