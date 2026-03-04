from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import GEMINI_API_KEY, LLM_MODEL, TEMPERATURE


def get_llm() -> ChatGoogleGenerativeAI:
    """Return a ChatGoogleGenerativeAI instance for use with LangChain agents."""
    return ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=TEMPERATURE,
    )


class LLMs:
    def __init__(self):
        self.llm = get_llm()

    def invoke(self, prompt: str) -> str:
        response = self.llm.invoke(prompt)
        return response.content

    def invoke_with_history(self, messages: list) -> str:
        response = self.llm.invoke(messages)
        return response.content