import React, { useState, useEffect } from 'react'
import { API_BASE } from '../api'

function getTodayString() {
  const today = new Date()
  const yyyy = today.getFullYear()
  const mm = String(today.getMonth() + 1).padStart(2, '0')
  const dd = String(today.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

export default function Bookings({ token }) {
  const [selectedDate, setSelectedDate] = useState(getTodayString())
  const [bookings, setBookings] = useState([])
  const [slots, setSlots] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchData(selectedDate)
  }, [selectedDate, token])

  const fetchData = async (date) => {
    setLoading(true)
    setError('')
    try {
      const headers = token ? { 'X-Admin-Token': token } : {}
      const [bookingsRes, slotsRes] = await Promise.all([
        fetch(`${API_BASE}/api/bookings`, { headers }),
        fetch(`${API_BASE}/api/slots?date=${date}`, { headers }),
      ])

      if (!bookingsRes.ok) throw new Error('Failed to fetch bookings')
      if (!slotsRes.ok) throw new Error('Failed to fetch slots')

      const allBookings = await bookingsRes.json()
      const slotsData = await slotsRes.json()

      const dateBookings = allBookings.filter((b) => b.booking_date === date)
      setBookings(dateBookings)
      setSlots(slotsData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bookings-page">
      <div className="card date-header">
        <label htmlFor="date-picker"><strong>Select Date:</strong></label>
        <input
          id="date-picker"
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        />
        <button className="btn btn-secondary" onClick={() => fetchData(selectedDate)}>
          Refresh
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2>Bookings on {selectedDate} ({bookings.length})</h2>
        {loading ? (
          <p>Loading bookings...</p>
        ) : bookings.length === 0 ? (
          <p className="empty-text">No bookings found for this date.</p>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Booking ID</th>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Start Time</th>
                  <th>End Time</th>
                  <th>Service</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {bookings.map((b) => (
                  <tr key={b.id}>
                    <td><code>{b.id}</code></td>
                    <td><strong>{b.user_name}</strong></td>
                    <td>{b.user_phone}</td>
                    <td>{b.start_time}</td>
                    <td>{b.end_time}</td>
                    <td>{b.service_type || '—'}</td>
                    <td>
                      <span className={`badge badge-${b.status}`}>
                        {b.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card">
        <h2>Slot Availability on {selectedDate}</h2>
        {loading ? (
          <p>Loading slots...</p>
        ) : slots.length === 0 ? (
          <p className="empty-text">No slots generated for this date.</p>
        ) : (
          <div className="slots-grid">
            {slots.map((s, idx) => {
              if (s.is_break) {
                return (
                  <div key={idx} className="slot-card slot-break">
                    <div className="slot-time">
                      {s.start_time} – {s.end_time}
                    </div>
                    <div className="slot-count break-text">
                      <strong>{s.break_name || 'Scheduled Break'}</strong>
                    </div>
                    <div className="slot-badge">
                      <span className="badge badge-break">BREAK</span>
                    </div>
                  </div>
                )
              }

              const isFull = s.booked_count >= s.capacity || !s.is_available
              return (
                <div
                  key={idx}
                  className={`slot-card ${isFull ? 'slot-full' : 'slot-available'}`}
                >
                  <div className="slot-time">
                    {s.start_time} – {s.end_time}
                  </div>
                  <div className="slot-count">
                    Booked: <strong>{s.booked_count}</strong> / {s.capacity}
                  </div>
                  <div className="slot-badge">
                    {isFull ? (
                      <span className="badge badge-full">FULL</span>
                    ) : (
                      <span className="badge badge-available">AVAILABLE</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
