import React from 'react'
import { Routes, Route, Link, Navigate } from 'react-router-dom'
import Bookings from './pages/Bookings'
import Settings from './pages/Settings'

export default function App() {
  return (
    <div className="app-container">
      <header className="navbar">
        <div className="nav-brand">WhatsApp Booking Admin</div>
        <nav className="nav-links">
          <Link to="/bookings" className="nav-link">Bookings & Slots</Link>
          <Link to="/settings" className="nav-link">Business Settings</Link>
        </nav>
      </header>

      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/bookings" replace />} />
          <Route path="/bookings" element={<Bookings />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
