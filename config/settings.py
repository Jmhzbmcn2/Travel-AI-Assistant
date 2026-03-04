"""
Application settings — loads environment variables and configures LLM.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

# ── SerpAPI ──────────────────────────────────────────
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# ── Makcorps (optional) ─────────────────────────────
MAKCORPS_API_KEY = os.getenv("MAKCORPS_API_KEY")

# ── OpenWeatherMap ──────────────────────────────────
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

# ── Tavily Search ──────────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ── Defaults ─────────────────────────────────────────
DEFAULT_CURRENCY = "VND"
MAX_FLEXIBLE_DAYS = 3  # ±3 days for flexible date search
