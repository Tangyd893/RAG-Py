"""小米 MiMo LLM Provider 适配器——通过 HTTP API 调用。"""

import httpx

from app.core.config import settings
from app.infrastructure.providers.llm.base import GenerationResult


class MimoLlmProvider:
    """MiMo LLM 适配器——OpenAI 兼容 API 格式。"""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int = 60,
    ):
        self.base_url = base_url or settings.mimo_base_url
        self.model = model or settings.mimo_model
        self.api_key = api_key or settings.mimo_api_key
        self.timeout = timeout or settings.mimo_timeout_seconds

    async def generate(
        self, messages: list[dict], temperature: float = 0.2
    ) -> GenerationResult:
        if not self.base_url:
            return GenerationResult(
                text="LLM 服务未配置，请设置 MIMO_BASE_URL。",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": 1024,
                    },
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                choice = data["choices"][0]
                usage = data.get("usage", {})
                return GenerationResult(
                    text=choice["message"]["content"],
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                )
        except Exception:
            return GenerationResult(
                text="LLM 服务暂时不可用，请稍后重试。",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
            )
