import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Header, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app import config, db, tools
from app import reminders as reminder_engine
from app.models import (
    Booking,
    BookingCreate,
    BookingCancelRequest,
    BookingRescheduleRequest,
    TimeSlot,
    Settings,
    ChatRequest,
    ChatResponse,
    LoginRequest,
)
from app.agent import run_booking_agent

logger = logging.getLogger(__name__)

# Initialize DB on startup
db.init_db()


async def _reminder_loop():
    """Run send_due_reminders once immediately, then repeat every hour."""
    while True:
        try:
            count = reminder_engine.send_due_reminders()
            logger.info("Reminder loop: processed %d reminder(s)", count)
        except Exception as exc:
            logger.error("Reminder loop error: %s", exc, exc_info=True)
        await asyncio.sleep(3600)  # 1 hour


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_reminder_loop())
    yield


app = FastAPI(title=config.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_admin_token(x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token")):
    if not x_admin_token or x_admin_token != config.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/api/login")
def login(req: LoginRequest):
    if req.phone == config.ADMIN_PHONE and req.password == config.ADMIN_PASSWORD:
        return {"success": True, "token": config.ADMIN_PASSWORD}
    return JSONResponse(status_code=401, content={"success": False})


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/api/settings", response_model=Settings, dependencies=[Depends(verify_admin_token)])
def get_settings():
    return db.get_settings()


@app.put("/api/settings", response_model=Settings, dependencies=[Depends(verify_admin_token)])
def update_settings(settings: Settings):
    if tools.time_to_minutes(settings.close_time) <= tools.time_to_minutes(settings.open_time):
        raise HTTPException(status_code=400, detail="close_time must be later than open_time")
    if settings.slot_duration_minutes <= 0:
        raise HTTPException(status_code=400, detail="slot_duration_minutes must be greater than 0")
    if settings.capacity < 1:
        raise HTTPException(status_code=400, detail="capacity must be 1 or more")

    for b in settings.breaks:
        if b.duration_minutes <= 0:
            raise HTTPException(status_code=400, detail=f"Break duration for '{b.name}' must be greater than 0")

    breaks_data = [b.model_dump() if hasattr(b, "model_dump") else b.dict() for b in settings.breaks]

    return db.update_settings(
        open_time=settings.open_time,
        close_time=settings.close_time,
        slot_duration_minutes=settings.slot_duration_minutes,
        capacity=settings.capacity,
        breaks=breaks_data,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        history = db.get_history(req.user_phone) if req.user_phone else []
        reply_text = await run_booking_agent(req.message, req.user_phone, history)
        if req.user_phone:
            db.save_message(req.user_phone, "user", req.message)
            db.save_message(req.user_phone, "assistant", reply_text)
        return ChatResponse(reply=reply_text)
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        return ChatResponse(
            reply="Sorry, I encountered an error processing your request. Please try again later."
        )



@app.get("/api/slots", response_model=List[TimeSlot], dependencies=[Depends(verify_admin_token)])
def get_slots(date: str = Query(..., description="YYYY-MM-DD")):
    return tools.check_available_slots(date)


@app.get("/api/bookings", response_model=List[Booking], dependencies=[Depends(verify_admin_token)])
def get_bookings(phone: Optional[str] = None):
    if phone:
        return db.get_bookings_by_phone(phone)
    return db.list_all_bookings()


@app.post("/api/bookings", response_model=Booking, dependencies=[Depends(verify_admin_token)])
def create_booking(booking_in: BookingCreate):
    result = tools.book_appointment_tool(
        user_name=booking_in.user_name,
        user_phone=booking_in.user_phone,
        booking_date=booking_in.booking_date,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        service_type=booking_in.service_type,
        notes=booking_in.notes,
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result["booking"]


@app.post("/api/bookings/cancel", dependencies=[Depends(verify_admin_token)])
def cancel_booking(req: BookingCancelRequest):
    result = tools.cancel_appointment_tool(req.booking_id, req.reason)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/api/bookings/reschedule", dependencies=[Depends(verify_admin_token)])
def reschedule_booking(req: BookingRescheduleRequest):
    result = tools.reschedule_appointment_tool(
        req.booking_id,
        req.new_date,
        req.new_start_time,
        req.new_end_time
    )
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.post("/api/reminders/run", dependencies=[Depends(verify_admin_token)])
def run_reminders():
    count = reminder_engine.send_due_reminders()
    return {"sent": count}
