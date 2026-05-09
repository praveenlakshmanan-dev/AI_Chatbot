from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

# Embeddings must go through the Amzur LiteLLM proxy.
embeddings = OpenAIEmbeddings(
    model=settings.LITELLM_EMBEDDING_MODEL,
    base_url=settings.LITELLM_PROXY_URL,
    api_key=settings.LITELLM_API_KEY,
)
