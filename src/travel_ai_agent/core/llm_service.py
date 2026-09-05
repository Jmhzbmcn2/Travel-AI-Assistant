from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from travel_ai_agent.config.settings import (
    GEMINI_API_KEY,
    LLM_MODEL,
    LLM_PROVIDER,
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_BASE_URL,
    OPENROUTER_SITE_URL,
    TEMPERATURE,
)

# Cost per 1M tokens (USD) — approximate rates
MODEL_COSTS: dict[str, dict[str, float]] = {
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "google/gemini-2.5-flash-lite": {"input": 0.075, "output": 0.30},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost from token usage."""
    rates = MODEL_COSTS.get(model, {"input": 0.15, "output": 0.60})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


def get_llm() -> BaseChatModel:
    """Return the configured chat model for use with LangChain agents."""
    if LLM_PROVIDER == "openrouter":
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER=openrouter")

        return ChatOpenAI(
            model=LLM_MODEL,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=TEMPERATURE,
            default_headers={
                "HTTP-Referer": OPENROUTER_SITE_URL,
                "X-Title": OPENROUTER_APP_NAME,
            },
        )

    if LLM_PROVIDER != "gemini":
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER=gemini")

    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=TEMPERATURE,
    )


def track_llm_usage(response, session_id: str | None = None) -> dict:
    """Extract token usage from LLM response and optionally record to session store.

    Returns dict with model, input_tokens, output_tokens, cost_usd.
    """
    usage_meta = getattr(response, "usage_metadata", None) or {}
    if isinstance(usage_meta, dict):
        input_tokens = usage_meta.get("input_tokens", 0)
        output_tokens = usage_meta.get("output_tokens", 0)
    else:
        input_tokens = getattr(usage_meta, "input_tokens", 0) or 0
        output_tokens = getattr(usage_meta, "output_tokens", 0) or 0

    cost_usd = _estimate_cost(LLM_MODEL, input_tokens, output_tokens)
    result = {
        "model": LLM_MODEL,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6),
    }

    if session_id:
        try:
            from travel_ai_agent.api.services.session_store import SessionStore
            store = SessionStore()
            store.add_llm_usage(session_id, LLM_MODEL, input_tokens, output_tokens, cost_usd)
        except Exception:
            pass

    return result


class LLMs:
    def __init__(self):
        self.llm = get_llm()

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content

    def invoke_with_history(self, messages: list) -> str:
        response = self.llm.invoke(messages)
        return response.content
