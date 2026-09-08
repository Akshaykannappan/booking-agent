from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelRequest, ModelResponse, UserPromptPart, TextPart, ModelMessage
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from app import config, tools

# Groq Model setup
model = GroqModel(
    config.LLM_MODEL,
    provider=GroqProvider(api_key=config.GROQ_API_KEY),
)

booking_agent = Agent(
    model=model,
)



@booking_agent.system_prompt
def get_system_prompt(ctx: RunContext[None]) -> str:
    now_dt = tools.now()
    today_str = now_dt.strftime("%Y-%m-%d")
    tomorrow_str = (now_dt + timedelta(days=1)).strftime("%Y-%m-%d")
    return f"""You are a helpful and concise WhatsApp appointment booking assistant.
Your job is to assist customers with booking, checking availability, rescheduling, looking up, and cancelling appointments.

Context:
- Today's date is: {today_str}
- Tomorrow's date is: {tomorrow_str}
- Always use the exact date string "{tomorrow_str}" for tomorrow in both your replies and tool parameters. Never guess or change the month.
- The customer's WhatsApp phone number is already verified from chat context. NEVER ask the customer for their phone number.

CRITICAL BOOKING FLOW (DO NOT DEVIATE):
Follow this exact sequence:
1. When customer requests a booking without their name:
   - Reply asking ONLY for their full name: "I can help with that! Could you please provide your full name?"
2. When customer provides their name (along with requested date and time):
   - Check slot availability using `get_available_slots`.
   - Do NOT ask any questions about service type or notes. Output ONLY the confirmation question using the customer's name, date, and requested time:
     "I have an appointment for <name> on <date> at <time>. Would you like me to confirm this booking?"
   - DO NOT call `book_appointment` in this step. Wait for confirmation.
3. When customer replies with "yes", "confirm", "sure", or "ok":
   - You MUST call the `book_appointment` tool with: user_name=<name>, user_phone=<customer phone>, booking_date=<date>, start_time=<time>, service_type=""
   - Reply with the confirmed booking details and the Booking ID returned by the tool.

Rules:
- NEVER ask for phone number.
- NEVER ask for or invent a service_type (leave service_type="").
- Break times (such as Lunch Break) cannot be booked. If a slot is marked as a break or during a break, inform the customer politely and suggest the nearest available slot.
- Never output raw JSON in your text responses.
- Keep messages short and friendly for WhatsApp.
"""








@booking_agent.tool
def resolve_date(ctx: RunContext[None], text: str) -> Dict[str, Any]:
    """
    Resolve words like 'today', 'tomorrow', 'friday', 'next monday', or a date string into a verified YYYY-MM-DD date.
    Always call this tool whenever the customer mentions any relative or named date. Never compute dates yourself.
    """
    resolved = tools.resolve_date(text)
    if resolved:
        return {"success": True, "date": resolved}
    return {
        "success": False,
        "message": f"Could not resolve date '{text}'. Please ask the customer to clarify the date (YYYY-MM-DD).",
    }


@booking_agent.tool
def get_available_slots(ctx: RunContext[None], query_date: str) -> List[Dict[str, Any]]:
    """
    Check all available appointment slots for a specific date (YYYY-MM-DD).
    """
    slots = tools.check_available_slots(query_date)

    result = []
    for s in slots:
        result.append({
            "slot_date": s.slot_date,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "is_available": s.is_available,
            "is_break": s.is_break,
            "break_name": s.break_name,
        })
    return result


@booking_agent.tool
def book_appointment(
    ctx: RunContext[None],
    user_name: str,
    user_phone: str,
    booking_date: str,
    start_time: str,
    service_type: str = "",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Book an appointment.
    CRITICAL: ONLY call this tool AFTER the customer has explicitly confirmed (said 'yes'/'confirm' to the summary).
    service_type: MUST be empty string "" unless customer explicitly requested a specific service. NEVER pass 'Consultation'.
    """
    return tools.book_appointment_tool(
        user_name=user_name,
        user_phone=user_phone,
        booking_date=booking_date,
        start_time=start_time,
        service_type=service_type or "",
        notes=notes,
    )





@booking_agent.tool
def cancel_appointment(ctx: RunContext[None], booking_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Cancel a booking by booking ID.
    """
    return tools.cancel_appointment_tool(booking_id=booking_id, reason=reason)


@booking_agent.tool
def reschedule_appointment(
    ctx: RunContext[None],
    booking_id: str,
    new_date: str,
    new_start_time: str,
) -> Dict[str, Any]:
    """
    Reschedule an existing booking to a new date and start time.
    """
    return tools.reschedule_appointment_tool(
        booking_id=booking_id,
        new_date=new_date,
        new_start_time=new_start_time,
    )


@booking_agent.tool
def lookup_booking(ctx: RunContext[None], booking_id: str) -> Dict[str, Any]:
    """
    Look up booking details by booking ID. Only call when customer asks for a specific booking ID.
    """
    return tools.get_booking_details_tool(booking_id=booking_id)


@booking_agent.tool
def lookup_user_bookings(ctx: RunContext[None], phone: str) -> Dict[str, Any]:
    """
    Look up all existing appointments for a customer phone.
    ONLY call this if the customer asks to view/check their past or existing appointments.
    Do NOT call this when a customer is making a new booking.
    """
    return tools.list_user_bookings_tool(phone=phone)



def build_message_history(history_records: List[Dict[str, Any]]) -> List[ModelMessage]:
    messages: List[ModelMessage] = []
    for h in history_records:
        role = h.get("role")
        content = h.get("message", "")
        if role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=content)]))
        elif role == "assistant":
            messages.append(ModelResponse(parts=[TextPart(content=content)]))
    return messages


async def run_booking_agent(
    message: str,
    user_phone: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Run the agent with message, optional user phone context, and message history."""
    message_history: Optional[List[ModelMessage]] = None
    if history:
        message_history = build_message_history(history)

    full_prompt = message
    if user_phone:
        full_prompt = f"Customer Phone: {user_phone}\nMessage: {message}"

    result = await booking_agent.run(full_prompt, message_history=message_history)
    if hasattr(result, "output"):
        return str(result.output)
    if hasattr(result, "data"):
        return str(result.data)
    return str(result)

