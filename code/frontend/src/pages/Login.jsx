import React, { useState } from 'react'
import { API_BASE } from '../api'

export default function Login({ onLogin }) {
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password }),
      })

      const data = await res.json()

      if (res.ok && data.success && data.token) {
        onLogin(data.token)
      } else {
        setError('Invalid phone number or password.')
      }
    } catch (err) {
      setError(err.message || 'Failed to log in.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <header className="navbar">
        <div className="nav-brand">WhatsApp Booking Admin</div>
      </header>
      <main className="content" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <div className="card" style={{ width: '100%', maxWidth: '400px' }}>
          <h2>Admin Login</h2>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div className="form-group">
              <label htmlFor="login-phone">Phone Number</label>
              <input
                id="login-phone"
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="1234567890"
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••"
                required
              />
            </div>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ width: '100%', marginTop: '0.5rem' }}
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
