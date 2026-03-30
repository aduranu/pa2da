import json
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.llm = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=0.0,
            max_tokens=4096,
        )

    def invoke(self, system: str, user: str) -> str:
        """Send a system + user prompt and return the text response."""
        messages = [SystemMessage(content=system), HumanMessage(content=user)]
        response = self.llm.invoke(messages)
        return response.content

    def invoke_json(self, system: str, user: str) -> list | dict:
        """Send a prompt expecting JSON back. Retries once on parse failure."""
        from ken.llm.prompts import JSON_RETRY

        text = self.invoke(system, user)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON, retrying...")
            text = self.invoke(system, f"{user}\n\n{JSON_RETRY}")
            return json.loads(text)
