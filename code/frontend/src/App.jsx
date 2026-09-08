import React, { useState } from 'react'
import { Routes, Route, Link, Navigate } from 'react-router-dom'
import Bookings from './pages/Bookings'
import Settings from './pages/Settings'
import Chat from './pages/Chat'
import Login from './pages/Login'

export default function App() {
  const [token, setToken] = useState('')

  if (!token) {
    return <Login onLogin={setToken} />
  }

  return (
    <div className="app-container">
      <header className="navbar">
        <div className="nav-brand">WhatsApp Booking Admin</div>
        <nav className="nav-links">
          <Link to="/bookings" className="nav-link">Bookings & Slots</Link>
          <Link to="/settings" className="nav-link">Business Settings</Link>
          <Link to="/chat" className="nav-link">Chat</Link>
        </nav>
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/bookings" replace />} />
          <Route path="/bookings" element={<Bookings token={token} />} />
          <Route path="/settings" element={<Settings token={token} />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </main>
    </div>
  )
}
