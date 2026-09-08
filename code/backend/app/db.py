import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from app import config
from app.models import BookingCreate


def generate_booking_id() -> str:
    return f"BK-{uuid.uuid4().hex[:8].upper()}"


def get_db():
    conn = sqlite3.connect(config.DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("""

        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            user_phone TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            service_type TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_booking_date ON bookings(booking_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_phone ON bookings(user_phone);")

    # Add reminder_sent column if it doesn't exist (safe migration for existing DBs)
    existing_cols = [row[1] for row in cursor.execute("PRAGMA table_info(bookings)").fetchall()]
    if "reminder_sent" not in existing_cols:
        cursor.execute("ALTER TABLE bookings ADD COLUMN reminder_sent INTEGER NOT NULL DEFAULT 0")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            open_time TEXT NOT NULL,
            close_time TEXT NOT NULL,
            slot_duration_minutes INTEGER NOT NULL,
            capacity INTEGER NOT NULL
        );
    """)
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO settings (open_time, close_time, slot_duration_minutes, capacity) VALUES (?, ?, ?, ?)",
            ("09:00", "17:00", 30, 1)
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS breaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL
        );
    """)
    cursor.execute("SELECT COUNT(*) FROM breaks")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO breaks (name, start_time, end_time, duration_minutes) VALUES (?, ?, ?, ?)",
            ("Lunch Break", "13:00", "14:00", 60)
        )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_phone TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_history_phone ON chat_history(user_phone);")

    conn.commit()
    conn.close()


def save_message(user_phone: str, role: str, message: str) -> None:
    now_str = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (user_phone, role, message, created_at) VALUES (?, ?, ?, ?)",
        (user_phone, role, message, now_str)
    )
    conn.commit()
    conn.close()


def get_history(user_phone: str, limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT role, message, created_at FROM (
            SELECT id, role, message, created_at FROM chat_history
            WHERE user_phone = ?
            ORDER BY id DESC LIMIT ?
        ) ORDER BY id ASC
        """,
        (user_phone, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_breaks() -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, start_time, end_time, duration_minutes FROM breaks ORDER BY start_time ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_settings() -> Dict[str, Any]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT open_time, close_time, slot_duration_minutes, capacity FROM settings LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    breaks = get_breaks()
    if row:
        res = dict(row)
        res["breaks"] = breaks
        return res
    return {
        "open_time": "09:00",
        "close_time": "17:00",
        "slot_duration_minutes": 30,
        "capacity": 1,
        "breaks": breaks,
    }


def update_settings(
    open_time: Optional[str] = None,
    close_time: Optional[str] = None,
    slot_duration_minutes: Optional[int] = None,
    capacity: Optional[int] = None,
    breaks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    current = get_settings()
    new_open = open_time if open_time is not None else current["open_time"]
    new_close = close_time if close_time is not None else current["close_time"]
    new_duration = slot_duration_minutes if slot_duration_minutes is not None else current["slot_duration_minutes"]
    new_capacity = capacity if capacity is not None else current["capacity"]

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings")
    cursor.execute(
        "INSERT INTO settings (open_time, close_time, slot_duration_minutes, capacity) VALUES (?, ?, ?, ?)",
        (new_open, new_close, new_duration, new_capacity),
    )

    if breaks is not None:
        cursor.execute("DELETE FROM breaks")
        for b in breaks:
            b_name = b.get("name", "Break")
            b_start = b.get("start_time", "13:00")
            b_dur = int(b.get("duration_minutes", 60))
            b_end = b.get("end_time")
            if not b_end:
                sh, sm = map(int, b_start.split(":"))
                total_m = sh * 60 + sm + b_dur
                b_end = f"{(total_m // 60) % 24:02d}:{total_m % 60:02d}"
            cursor.execute(
                "INSERT INTO breaks (name, start_time, end_time, duration_minutes) VALUES (?, ?, ?, ?)",
                (b_name, b_start, b_end, b_dur),
            )

    conn.commit()
    conn.close()
    return get_settings()


def create_booking(booking_in: BookingCreate) -> Dict[str, Any]:
    now_str = datetime.utcnow().isoformat()
    booking_id = generate_booking_id()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bookings (
            id, user_name, user_phone, booking_date,
            start_time, end_time, service_type, notes, status,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            booking_id,
            booking_in.user_name,
            booking_in.user_phone,
            booking_in.booking_date,
            booking_in.start_time,
            booking_in.end_time or "",
            booking_in.service_type or "",
            booking_in.notes or "",
            "confirmed",
            now_str,
            now_str,
        ),
    )
    conn.commit()
    conn.close()

    return {
        "id": booking_id,
        "user_name": booking_in.user_name,
        "user_phone": booking_in.user_phone,
        "booking_date": booking_in.booking_date,
        "start_time": booking_in.start_time,
        "end_time": booking_in.end_time,
        "service_type": booking_in.service_type or "",
        "notes": booking_in.notes,
        "status": "confirmed",
        "created_at": now_str,
        "updated_at": now_str,
    }



def get_booking_by_id(booking_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def get_bookings_by_date(date_str: str) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM bookings WHERE booking_date = ? AND status != 'cancelled' ORDER BY start_time ASC",
        (date_str,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_bookings_by_phone(phone: str) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM bookings WHERE user_phone = ? ORDER BY booking_date DESC, start_time DESC",
        (phone,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def list_all_bookings(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def cancel_booking_in_db(booking_id: str, reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
    now_str = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    notes = row["notes"] or ""
    if reason:
        notes = f"{notes} | Cancel Reason: {reason}".strip(" |")

    cursor.execute(
        "UPDATE bookings SET status = 'cancelled', notes = ?, updated_at = ? WHERE id = ?",
        (notes, now_str, booking_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return dict(updated_row) if updated_row else None


def reschedule_booking_in_db(
    booking_id: str,
    new_date: str,
    new_start_time: str,
    new_end_time: str
) -> Optional[Dict[str, Any]]:
    now_str = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    cursor.execute(
        """
        UPDATE bookings
        SET booking_date = ?, start_time = ?, end_time = ?, status = 'rescheduled',
            reminder_sent = 0, updated_at = ?
        WHERE id = ?
        """,
        (new_date, new_start_time, new_end_time, now_str, booking_id)
    )
    conn.commit()
    cursor.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return dict(updated_row) if updated_row else None


def get_bookings_needing_reminder(target_date: str) -> List[Dict[str, Any]]:
    """Return confirmed/rescheduled bookings on target_date where reminder has not been sent."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM bookings
        WHERE booking_date = ?
          AND status IN ('confirmed', 'rescheduled')
          AND reminder_sent = 0
        ORDER BY start_time ASC
        """,
        (target_date,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def mark_reminder_sent(booking_id: str) -> None:
    """Mark a booking's reminder as sent."""
    now_str = datetime.utcnow().isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bookings SET reminder_sent = 1, updated_at = ? WHERE id = ?",
        (now_str, booking_id)
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
