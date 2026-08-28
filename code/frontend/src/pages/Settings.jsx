
import React, { useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000'

export default function Settings() {
  const [form, setForm] = useState({
    open_time: '',
    close_time: '',
    slot_duration_minutes: 30,
    capacity: 1,
  })
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState({ type: '', text: '' })

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const res = await fetch(`${API_BASE}/api/settings`)
      if (!res.ok) throw new Error('Failed to load settings')
      const data = await res.json()
      setForm({
        open_time: data.open_time || '09:00',
        close_time: data.close_time || '17:00',
        slot_duration_minutes: data.slot_duration_minutes || 30,
        capacity: data.capacity || 1,
      })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: name === 'slot_duration_minutes' || name === 'capacity' ? parseInt(value, 10) || 0 : value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    try {
      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to update settings')
      }
      setForm(data)
      setMessage({ type: 'success', text: 'Settings updated successfully!' })
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  if (loading) {
    return <div className="card">Loading settings...</div>
  }

  return (
    <div className="card">
      <h2>Business Settings</h2>
      {message.text && (
        <div className={`alert alert-${message.type}`}>
          {message.text}
        </div>
      )}
      <form onSubmit={handleSubmit} className="form-grid">
        <div className="form-group">
          <label>Open Time (HH:MM)</label>
          <input
            type="text"
            name="open_time"
            value={form.open_time}
            onChange={handleChange}
            placeholder="09:00"
            required
          />
        </div>

        <div className="form-group">
          <label>Close Time (HH:MM)</label>
          <input
            type="text"
            name="close_time"
            value={form.close_time}
            onChange={handleChange}
            placeholder="17:00"
            required
          />
        </div>

        <div className="form-group">
          <label>Slot Duration (minutes)</label>
          <input
            type="number"
            name="slot_duration_minutes"
            value={form.slot_duration_minutes}
            onChange={handleChange}
            min="1"
            required
          />
        </div>

        <div className="form-group">
          <label>Capacity (customers per slot)</label>
          <input
            type="number"
            name="capacity"
            value={form.capacity}
            onChange={handleChange}
            min="1"
            required
          />
        </div>

        <button type="submit" className="btn btn-primary">
          Save Settings
        </button>
      </form>
    </div>
  )
}
