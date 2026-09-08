import React, { useState, useEffect } from 'react'
import { API_BASE } from '../api'

export default function Settings({ token }) {
  const [form, setForm] = useState({
    open_time: '',
    close_time: '',
    slot_duration_minutes: 30,
    capacity: 1,
    breaks: [],
  })
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState({ type: '', text: '' })

  useEffect(() => {
    fetchSettings()
  }, [token])

  const fetchSettings = async () => {
    try {
      setLoading(true)
      const headers = token ? { 'X-Admin-Token': token } : {}
      const res = await fetch(`${API_BASE}/api/settings`, { headers })
      if (!res.ok) throw new Error('Failed to load settings')
      const data = await res.json()
      setForm({
        open_time: data.open_time || '09:00',
        close_time: data.close_time || '17:00',
        slot_duration_minutes: data.slot_duration_minutes || 30,
        capacity: data.capacity || 1,
        breaks: data.breaks || [],
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

  const handleBreakChange = (index, field, value) => {
    setForm((prev) => {
      const updated = [...prev.breaks]
      updated[index] = {
        ...updated[index],
        [field]: field === 'duration_minutes' ? parseInt(value, 10) || 0 : value,
      }
      return { ...prev, breaks: updated }
    })
  }

  const handleAddBreak = () => {
    setForm((prev) => ({
      ...prev,
      breaks: [
        ...prev.breaks,
        { name: 'Lunch Break', start_time: '13:00', duration_minutes: 60 },
      ],
    }))
  }

  const handleRemoveBreak = (index) => {
    setForm((prev) => ({
      ...prev,
      breaks: prev.breaks.filter((_, i) => i !== index),
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'X-Admin-Token': token } : {}),
      }
      const res = await fetch(`${API_BASE}/api/settings`, {
        method: 'PUT',
        headers,
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
      <form onSubmit={handleSubmit} className="settings-form">
        <div className="form-grid">
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
        </div>

        <div className="breaks-section">
          <div className="breaks-header">
            <h3>Break Times (Blocked from Booking)</h3>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={handleAddBreak}
            >
              + Add Break
            </button>
          </div>
          <p className="section-help">
            Slots during these intervals are marked as BREAK and cannot be booked.
          </p>

          {(!form.breaks || form.breaks.length === 0) ? (
            <p className="empty-text">No break times scheduled.</p>
          ) : (
            <div className="breaks-list">
              {form.breaks.map((b, idx) => (
                <div key={idx} className="break-item">
                  <div className="form-group break-field-name">
                    <label>Break Name</label>
                    <input
                      type="text"
                      value={b.name}
                      placeholder="e.g. Lunch Break"
                      onChange={(e) => handleBreakChange(idx, 'name', e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group break-field-time">
                    <label>Start (HH:MM)</label>
                    <input
                      type="text"
                      value={b.start_time}
                      placeholder="13:00"
                      onChange={(e) => handleBreakChange(idx, 'start_time', e.target.value)}
                      required
                    />
                  </div>
                  <div className="form-group break-field-dur">
                    <label>Duration (min)</label>
                    <input
                      type="number"
                      value={b.duration_minutes}
                      min="1"
                      onChange={(e) => handleBreakChange(idx, 'duration_minutes', e.target.value)}
                      required
                    />
                  </div>
                  <button
                    type="button"
                    className="btn btn-danger btn-sm remove-break-btn"
                    onClick={() => handleRemoveBreak(idx)}
                    title="Remove break"
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <button type="submit" className="btn btn-primary save-btn">
          Save Settings
        </button>
      </form>
    </div>
  )
}
