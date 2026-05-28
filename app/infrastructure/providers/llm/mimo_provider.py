class MimoLlmProvider:
    """MiMo provider adapter placeholder (config-driven)."""

    def __init__(self, base_url: str, model: str, api_key: str) -> None:
        self.base_url = base_url
        self.model = model
        self.api_key = api_key

    async def generate(self, prompt: str) -> str:
        # TODO: integrate real MiMo API call.
        return "Not implemented yet."
