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


# Database & timezone settings
DB_PATH = os.getenv("DB_PATH", "bookings.db")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

# Admin Auth
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "1234567890")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")


