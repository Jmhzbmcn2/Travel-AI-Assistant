"""
Application settings — loads environment variables and configures LLM.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5173")
OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Travel AI Agent")
DEFAULT_LLM_MODEL = (
    "google/gemini-2.5-flash-lite"
    if LLM_PROVIDER == "openrouter"
    else "gemini-2.5-flash"
)
LLM_MODEL = os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))

# ── SerpAPI ──────────────────────────────────────────
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# ── Makcorps (optional) ─────────────────────────────
MAKCORPS_API_KEY = os.getenv("MAKCORPS_API_KEY")

# ── OpenWeatherMap ──────────────────────────────────
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")

# ── Tavily Search ──────────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# ── Demo / Fixture Policy ────────────────────────────
# When DEMO_MODE=false (default), providers return empty lists on failure
# instead of fixture fallbacks. Fixtures are only used in demo/test mode.
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("true", "1")

# ── Defaults ─────────────────────────────────────────
DEFAULT_CURRENCY = "VND"
MAX_FLEXIBLE_DAYS = 3  # ±3 days for flexible date search
