class BgeEmbeddingProvider:
    """BGE provider adapter placeholder."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # TODO: integrate real BGE embedding model.
        return [[0.0] * 3 for _ in texts]
