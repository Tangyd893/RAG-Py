"""BGE Re-ranker Provider——基于 Cross-Encoder 的重排序。"""

from app.application.services.retrieval_service import RetrievedChunk
from app.core.config import settings


class BgeRerankerProvider:
    """BGE Re-ranker 适配器——默认使用 BAAI/bge-reranker-v2-m3。"""

    def __init__(self, model_name: str | None = None, device: str | None = None):
        self.model_name = model_name or settings.reranker_model_name
        self.device = device or settings.reranker_device
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device=self.device)
            # CrossEncoder 没有 dims 属性，但 reranker 只输出分数，不需要维度。
        except ImportError:
            self._model = False

    async def rerank(
        self, query: str, chunks: list[RetrievedChunk], top_k: int | None = None
    ) -> list[RetrievedChunk]:
        """对候选 chunks 进行重排序，返回按新分数排序的结果。"""
        if not chunks:
            return []

        self._load_model()
        if not self._model or self._model is False:
            return chunks[:top_k] if top_k else chunks

        pairs = [(query, c.content) for c in chunks]
        scores = self._model.predict(pairs, show_progress_bar=False)

        # Pair each chunk with its rerank score
        scored = list(zip(chunks, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        top = top_k or len(chunks)
        result: list[RetrievedChunk] = []
        for rank, (chunk, score) in enumerate(scored[:top]):
            chunk.score = float(score)
            chunk.rank = rank + 1
            result.append(chunk)
        return result
