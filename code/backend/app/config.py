import os
from dotenv import load_dotenv

load_dotenv()

# App settings
APP_NAME = os.getenv("APP_NAME", "BookingAgentAPI")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# LLM settings (Groq)
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


# Database & slot settings
DB_PATH = os.getenv("DB_PATH", "bookings.db")
BUSINESS_START_HOUR = int(os.getenv("BUSINESS_START_HOUR", 8))
BUSINESS_LUNCH_START = int(os.getenv("BUSINESS_LUNCH_START", 13))
BUSINESS_LUNCH_END = int(os.getenv("BUSINESS_LUNCH_END", 14))
BUSINESS_END_HOUR = int(os.getenv("BUSINESS_END_HOUR", 20))
SLOT_DURATION_MINUTES = int(os.getenv("SLOT_DURATION_MINUTES", 30))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

