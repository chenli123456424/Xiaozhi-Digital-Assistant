"""
Tongyi LLM Wrapper using dashscope native SDK
"""
from typing import Optional, List, Generator
import dashscope
from dashscope import Generation
import logging

from config import settings

logger = logging.getLogger(__name__)


def _build_messages(history: list, user_message: str, system_prompt: str = None) -> list:
    """构建 dashscope messages 格式"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    for msg in history:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})
    return messages


class TongyiLLMWrapper:
    """Wrapper for Tongyi LLM using dashscope native SDK"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "qwen-max",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
    ):
        self.api_key = api_key or settings.dashscope_api_key
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        if not self.api_key:
            raise ValueError("DASHSCOPE_API_KEY is not configured")

        dashscope.api_key = self.api_key
        # 对话历史，格式：[{"role": "user"/"assistant", "content": "..."}]
        self.history: List[dict] = []
        logger.info(f"Tongyi LLM initialized with model: {self.model}")

    def chat(self, user_message: str) -> str:
        messages = _build_messages(self.history, user_message)
        response = Generation.call(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            result_format='message',
        )
        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}: {response.message}")
        content = response.output.choices[0].message.content
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": content})
        logger.info(f"Generated response: {content[:100]}...")
        return content

    def chat_with_system_prompt(self, user_message: str, system_prompt: str = None) -> str:
        messages = _build_messages(self.history, user_message, system_prompt)
        response = Generation.call(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            result_format='message',
        )
        if response.status_code != 200:
            raise RuntimeError(f"API error {response.status_code}: {response.message}")
        content = response.output.choices[0].message.content
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": content})
        return content

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        messages = _build_messages(self.history, user_message)
        responses = Generation.call(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            result_format='message',
            stream=True,
            incremental_output=True,
        )
        full_response = ""
        for resp in responses:
            if resp.status_code != 200:
                raise RuntimeError(f"API error {resp.status_code}: {resp.message}")
            chunk = resp.output.choices[0].message.content
            if chunk:
                full_response += chunk
                yield chunk
        self.history.append({"role": "user", "content": user_message})
        self.history.append({"role": "assistant", "content": full_response})
        logger.info(f"Streaming completed. Total length: {len(full_response)}")

    def clear_history(self):
        self.history = []
        logger.info("Conversation history cleared")

    def get_history(self) -> List[dict]:
        return self.history.copy()

    def set_model(self, model: str):
        self.model = model
        logger.info(f"Model changed to: {model}")


# Global instance
_llm_instance: Optional[TongyiLLMWrapper] = None


def get_llm() -> TongyiLLMWrapper:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = TongyiLLMWrapper(
            api_key=settings.dashscope_api_key,
            model=settings.model_name,
            temperature=settings.temperature,
            top_p=settings.top_p,
            max_tokens=settings.max_tokens,
        )
    return _llm_instance
