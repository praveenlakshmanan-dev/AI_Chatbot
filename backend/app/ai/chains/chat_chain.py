from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.ai.llm import llm

_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "chat_prompt.txt"
_PROMPT_TEMPLATE = _PROMPT_PATH.read_text(encoding="utf-8")

chat_prompt = PromptTemplate.from_template(_PROMPT_TEMPLATE)
chat_chain = chat_prompt | llm | StrOutputParser()
