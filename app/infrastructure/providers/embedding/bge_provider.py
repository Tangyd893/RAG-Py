"""BGE 向量化 Provider 适配器。"""

from app.core.config import settings


class BgeEmbeddingProvider:
    """BGE 嵌入模型适配器——默认使用 BAAI/bge-m3。"""

    def __init__(self, model_name: str | None = None, device: str | None = None):
        self.model_name = model_name or settings.bge_model_name
        self.device = device or settings.bge_device
        self.dimensions = 1024
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
            self.dimensions = self._model.get_sentence_embedding_dimension()
        except ImportError:
            self._model = False

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        self._load_model()
        if self._model and self._model is not False:
            embeddings = self._model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
            return embeddings.tolist()
        return [[0.0] * self.dimensions for _ in texts]

    async def embed_query(self, query: str) -> list[float]:
        self._load_model()
        if self._model and self._model is not False:
            embedding = self._model.encode(
                query, normalize_embeddings=True, show_progress_bar=False
            )
            return embedding.tolist()
        return [0.0] * self.dimensions
