from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Optional, Dict, Any
from app import config, db
from app.models import TimeSlot, BookingCreate


def now() -> datetime:
    tz_name = getattr(config, "TIMEZONE", "Asia/Kolkata")
    return datetime.now(ZoneInfo(tz_name))


import re


def resolve_time(text: str) -> str:
    if not text or not isinstance(text, str):
        return text
    cleaned = text.strip().lower().replace(".", "")
    try:
        t = datetime.strptime(cleaned, "%H:%M")
        return t.strftime("%H:%M")
    except ValueError:
        pass
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", cleaned)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridiem = match.group(3)
        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"
    return text


def add_minutes_to_time(time_str: str, minutes: int) -> str:
    time_str = resolve_time(time_str)
    t = datetime.strptime(time_str, "%H:%M")
    new_t = t + timedelta(minutes=minutes)
    return new_t.strftime("%H:%M")


def time_to_minutes(time_str: str) -> int:
    time_str = resolve_time(time_str)
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    return hours * 60 + minutes


def is_overlapping(start1: str, end1: str, start2: str, end2: str) -> bool:
    s1 = time_to_minutes(start1)
    e1 = time_to_minutes(end1)
    s2 = time_to_minutes(start2)
    e2 = time_to_minutes(end2)
    return max(s1, s2) < min(e1, e2)


def check_break_overlap(start_time: str, end_time: str, breaks: List[Dict[str, Any]]) -> Optional[str]:
    for b in breaks:
        b_start = b.get("start_time")
        b_end = b.get("end_time")
        if not b_end:
            b_dur = b.get("duration_minutes", 60)
            b_end = add_minutes_to_time(b_start, b_dur)
        if is_overlapping(start_time, end_time, b_start, b_end):
            return b.get("name", "Break")
    return None




def is_past_date(date_str: str) -> bool:
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        today = now().date()
        return d < today
    except ValueError:
        return False



def resolve_date(text: str) -> Optional[str]:
    if not text or not isinstance(text, str):
        return None
    cleaned = text.strip().lower()

    # If YYYY-MM-DD format is in the text
    match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", cleaned)
    if match:
        return match.group(0)

    today = now().date()


    if "tomorrow" in cleaned:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    if "today" in cleaned:
        return today.strftime("%Y-%m-%d")

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    for day_name, day_num in weekdays.items():
        if day_name in cleaned:
            current_weekday = today.weekday()
            days_ahead = day_num - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            target_date = today + timedelta(days=days_ahead)
            return target_date.strftime("%Y-%m-%d")

    months = {
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
        "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    # Match "august 29", "aug 29th", "29th august", "29 august"
    for m_name, m_num in months.items():
        if m_name in cleaned:
            day_match = re.search(r"\b(\d{1,2})(st|nd|rd|th)?\b", cleaned.replace(m_name, " "))
            if day_match:
                d_num = int(day_match.group(1))
                try:
                    target = datetime(today.year, m_num, d_num).date()
                    if target < today:
                        target = datetime(today.year + 1, m_num, d_num).date()
                    return target.strftime("%Y-%m-%d")
                except ValueError:
                    pass

    return None


def check_available_slots(query_date: str) -> List[TimeSlot]:
    resolved = resolve_date(query_date)
    if resolved:
        query_date = resolved

    if is_past_date(query_date):
        return []

    settings = db.get_settings()
    slot_duration = settings["slot_duration_minutes"]
    capacity = settings["capacity"]
    breaks = settings.get("breaks", [])
    start_minutes = time_to_minutes(settings["open_time"])
    end_minutes = time_to_minutes(settings["close_time"])

    existing_bookings = db.get_bookings_by_date(query_date)
    slots = []
    current_minutes = start_minutes

    while current_minutes + slot_duration <= end_minutes:
        s_hour = current_minutes // 60
        s_min = current_minutes % 60
        start_str = f"{s_hour:02d}:{s_min:02d}"

        e_total = current_minutes + slot_duration
        e_hour = e_total // 60
        e_min = e_total % 60
        end_str = f"{e_hour:02d}:{e_min:02d}"

        break_name = check_break_overlap(start_str, end_str, breaks)
        is_break = break_name is not None

        count = 0
        for b in existing_bookings:
            if is_overlapping(start_str, end_str, b["start_time"], b["end_time"]):
                count += 1

        slots.append(
            TimeSlot(
                slot_date=query_date,
                start_time=start_str,
                end_time=end_str,
                is_available=(not is_break) and (count < capacity),
                booked_count=count,
                capacity=capacity,
                is_break=is_break,
                break_name=break_name,
            )
        )

        current_minutes += slot_duration

    return slots


def book_appointment_tool(
    user_name: str,
    user_phone: str,
    booking_date: str,
    start_time: str,
    end_time: Optional[str] = None,
    service_type: Optional[str] = "",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    resolved = resolve_date(booking_date)
    if resolved:
        booking_date = resolved

    if is_past_date(booking_date):
        return {
            "success": False,
            "message": f"Cannot book appointments for past dates ({booking_date}).",
        }

    settings = db.get_settings()
    slot_duration = settings["slot_duration_minutes"]
    capacity = settings["capacity"]

    start_time = resolve_time(start_time)
    if not end_time:
        end_time = add_minutes_to_time(start_time, slot_duration)
    else:
        end_time = resolve_time(end_time)

    break_name = check_break_overlap(start_time, end_time, settings.get("breaks", []))
    if break_name:
        return {
            "success": False,
            "message": f"Cannot book appointment: Slot {start_time}-{end_time} is during {break_name}."
        }

    existing_bookings = db.get_bookings_by_date(booking_date)
    count = 0
    for b in existing_bookings:
        if is_overlapping(start_time, end_time, b["start_time"], b["end_time"]):
            count += 1

    if count >= capacity:
        return {
            "success": False,
            "message": f"Slot {start_time}-{end_time} on {booking_date} is fully booked."
        }

    booking_in = BookingCreate(
        user_name=user_name,
        user_phone=user_phone,
        booking_date=booking_date,
        start_time=start_time,
        end_time=end_time,
        service_type=service_type or "",
        notes=notes,
    )


    booking = db.create_booking(booking_in)
    return {
        "success": True,
        "message": f"Appointment booked for {user_name} on {booking_date} at {start_time}.",
        "booking": booking
    }


def cancel_appointment_tool(booking_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    booking = db.get_booking_by_id(booking_id)
    if not booking:
        return {"success": False, "message": f"Booking {booking_id} not found."}

    if booking["status"] == "cancelled":
        return {"success": False, "message": f"Booking {booking_id} is already cancelled."}

    updated = db.cancel_booking_in_db(booking_id, reason)
    return {
        "success": True,
        "message": f"Booking {booking_id} cancelled.",
        "booking": updated
    }


def reschedule_appointment_tool(
    booking_id: str,
    new_date: str,
    new_start_time: str,
    new_end_time: Optional[str] = None
) -> Dict[str, Any]:
    resolved = resolve_date(new_date)
    if resolved:
        new_date = resolved

    if is_past_date(new_date):
        return {
            "success": False,
            "message": f"Cannot reschedule to a past date ({new_date}).",
        }

    booking = db.get_booking_by_id(booking_id)
    if not booking:
        return {"success": False, "message": f"Booking {booking_id} not found."}

    settings = db.get_settings()
    slot_duration = settings["slot_duration_minutes"]
    capacity = settings["capacity"]

    new_start_time = resolve_time(new_start_time)
    if not new_end_time:
        new_end_time = add_minutes_to_time(new_start_time, slot_duration)
    else:
        new_end_time = resolve_time(new_end_time)

    break_name = check_break_overlap(new_start_time, new_end_time, settings.get("breaks", []))
    if break_name:
        return {
            "success": False,
            "message": f"Cannot reschedule appointment: Slot {new_start_time}-{new_end_time} is during {break_name}."
        }

    existing_bookings = db.get_bookings_by_date(new_date)
    count = 0
    for b in existing_bookings:
        if b["id"] != booking_id and is_overlapping(new_start_time, new_end_time, b["start_time"], b["end_time"]):
            count += 1

    if count >= capacity:
        return {
            "success": False,
            "message": f"Slot {new_start_time}-{new_end_time} on {new_date} is already occupied."
        }

    updated = db.reschedule_booking_in_db(booking_id, new_date, new_start_time, new_end_time)
    return {
        "success": True,
        "message": f"Booking {booking_id} rescheduled to {new_date} at {new_start_time}.",
        "booking": updated
    }


def get_booking_details_tool(booking_id: str) -> Dict[str, Any]:
    booking = db.get_booking_by_id(booking_id)
    if not booking:
        return {"found": False, "message": f"Booking {booking_id} not found."}
    return {"found": True, "booking": booking}


def list_user_bookings_tool(phone: str) -> Dict[str, Any]:
    bookings = db.get_bookings_by_phone(phone)
    return {
        "phone": phone,
        "count": len(bookings),
        "bookings": bookings
    }
