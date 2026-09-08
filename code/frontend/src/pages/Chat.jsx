import React, { useState } from 'react'
import { API_BASE } from '../api'

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async (e) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed || loading) return

    const userMessage = { sender: 'user', text: trimmed }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: trimmed,
          user_phone: 'test-user',
        }),
      })

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`)
      }

      const data = await response.json()
      setMessages((prev) => [
        ...prev,
        { sender: 'agent', text: data.reply || 'No reply received' },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          sender: 'error',
          text: `Error: ${err.message || 'Failed to send message'}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '600px' }}>
      <h2>Chat Simulator</h2>

      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          padding: '1rem',
          backgroundColor: '#f8fafc',
          borderRadius: '6px',
          border: '1px solid #e2e8f0',
          marginBottom: '1rem',
        }}
      >
        {messages.length === 0 && !loading && (
          <p className="empty-text" style={{ textAlign: 'center', margin: 'auto' }}>
            No messages yet. Send a message to start chatting with the booking assistant.
          </p>
        )}

        {messages.map((msg, idx) => {
          if (msg.sender === 'user') {
            return (
              <div
                key={idx}
                style={{
                  alignSelf: 'flex-end',
                  backgroundColor: '#2563eb',
                  color: '#ffffff',
                  padding: '0.6rem 1rem',
                  borderRadius: '12px 12px 2px 12px',
                  maxWidth: '75%',
                  wordBreak: 'break-word',
                }}
              >
                {msg.text}
              </div>
            )
          }

          if (msg.sender === 'error') {
            return (
              <div
                key={idx}
                className="alert alert-error"
                style={{
                  margin: '0.25rem 0',
                  alignSelf: 'stretch',
                }}
              >
                {msg.text}
              </div>
            )
          }

          return (
            <div
              key={idx}
              style={{
                alignSelf: 'flex-start',
                backgroundColor: '#e2e8f0',
                color: '#1e293b',
                padding: '0.6rem 1rem',
                borderRadius: '12px 12px 12px 2px',
                maxWidth: '75%',
                wordBreak: 'break-word',
                whiteSpace: 'pre-wrap',
              }}
            >
              {msg.text}
            </div>
          )
        })}

        {loading && (
          <div
            style={{
              alignSelf: 'flex-start',
              backgroundColor: '#e2e8f0',
              color: '#64748b',
              padding: '0.6rem 1rem',
              borderRadius: '12px 12px 12px 2px',
              maxWidth: '75%',
              fontStyle: 'italic',
            }}
          >
            ...
          </div>
        )}
      </div>

      <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.75rem' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '0.6rem 0.75rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '0.95rem',
          }}
        />
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !input.trim()}
          style={{ justifySelf: 'auto', gridColumn: 'auto' }}
        >
          Send
        </button>
      </form>
    </div>
  )
}
