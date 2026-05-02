from langchain_openai import ChatOpenAI

from app.core.config import settings

# Centralized LLM client: all AI requests must flow through LiteLLM proxy.
llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    base_url=settings.LITELLM_PROXY_URL,
    api_key=settings.LITELLM_API_KEY,
    timeout=30,
    max_retries=2,
)
