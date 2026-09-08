from typing import Optional, List
from pydantic import BaseModel, Field


class BreakTime(BaseModel):
    name: str = "Lunch Break"
    start_time: str = "13:00"
    duration_minutes: int = 60
    end_time: Optional[str] = None


class TimeSlot(BaseModel):
    slot_date: str
    start_time: str
    end_time: str
    is_available: bool = True
    booked_count: int = 0
    capacity: int = 1
    is_break: bool = False
    break_name: Optional[str] = None


class Settings(BaseModel):
    open_time: str = "09:00"
    close_time: str = "17:00"
    slot_duration_minutes: int = 30
    capacity: int = 1
    breaks: List[BreakTime] = []



class BookingCreate(BaseModel):
    user_name: str
    user_phone: str
    booking_date: str
    start_time: str
    end_time: Optional[str] = None
    service_type: Optional[str] = ""
    notes: Optional[str] = None


class Booking(BaseModel):
    id: str
    user_name: str
    user_phone: str
    booking_date: str
    start_time: str
    end_time: str
    service_type: Optional[str] = ""
    notes: Optional[str] = None
    status: str = "confirmed"
    created_at: str
    updated_at: str



class BookingRescheduleRequest(BaseModel):
    booking_id: str
    new_date: str
    new_start_time: str
    new_end_time: Optional[str] = None


class BookingCancelRequest(BaseModel):
    booking_id: str
    reason: str


class ChatRequest(BaseModel):
    message: str
    user_phone: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str


class LoginRequest(BaseModel):
    phone: str
    password: str
