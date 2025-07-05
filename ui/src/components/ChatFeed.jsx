import React, { useRef, useEffect, useState } from 'react'
import { useWebSocketData } from './WebSocketProvider'

function ChatFeed() {
  const { chat } = useWebSocketData()
  const [newMessage, setNewMessage] = useState('')
  const [selectedCharacter, setSelectedCharacter] = useState('max')
  const chatScrollRef = useRef(null)
  const chatEndRef = useRef(null)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [chat])

  const sendMessage = async (e) => {
    e.preventDefault()
    if (!newMessage.trim()) return
    try {
      setNewMessage('')
      await fetch('/api/tvshow/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          character_id: selectedCharacter,
          content: newMessage
        })
      })
    } catch (error) {
      // Optionally handle error
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

  const getMoodEmoji = (characterId) => {
    // This would be enhanced to fetch actual mood data
    const moodEmojis = {
      max: '😊',
      leo: '🤔',
      emma: '🤩',
      marvin: '😌'
    }
    return moodEmojis[characterId] || '😐'
  }

  return (
    <div className="chat-feed" style={{display: 'flex', flexDirection: 'column', height: '100%'}}>
      <div className="chat-messages" ref={chatScrollRef} style={{flex: 1, overflowY: 'auto', minHeight: 0}}>
        {chat.length === 0 ? (
          <div className="loading">No messages yet. Start the conversation!</div>
        ) : (
          chat.map((message, index) => (
            <div key={index} className="message">
              <div className="message-header">
                <div className="message-character">
                  {message.character_id === 'user' ? (
                    <span className="character-name" style={{ color: '#fff' }}>
                      You
                      {message.recipient && (
                        <span style={{ color: '#888', fontWeight: 400 }}> → {message.recipient.charAt(0).toUpperCase() + message.recipient.slice(1)}</span>
                      )}
                    </span>
                  ) : (
                    <>
                      <span className="character-name" style={{ color: getCharacterColor(message.character_id) }}>
                        {message.character_id.charAt(0).toUpperCase() + message.character_id.slice(1)}
                      </span>
                      <span className="mood-indicator" title="Character mood">
                        {getMoodEmoji(message.character_id)}
                      </span>
                    </>
                  )}
                </div>
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