"""LLM Provider 抽象接口。"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class GenerationResult:
    """LLM 生成结果——包含文本和 token 用量。"""
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMProvider(Protocol):
    """LLM Provider 抽象接口——配置驱动，不绑定具体厂商。"""

    async def generate(
        self, messages: list[dict], temperature: float = 0.2
    ) -> GenerationResult:
        """根据消息列表生成回答。"""
        ...
