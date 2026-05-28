"""ChromaDB 向量存储适配器。"""

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.infrastructure.vector_store.base import VectorPoint


class ChromaVectorStore:
    """ChromaDB 向量存储实现——通过 HTTP 客户端连接 Chroma 服务。"""

    def __init__(self, host: str, port: int):
        self.client = chromadb.HttpClient(
            host=host, port=port, settings=ChromaSettings(anonymized_telemetry=False)
        )

    async def ensure_collection(self, name: str, dimension: int) -> None:
        self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(
        self, collection_name: str, points: list[VectorPoint]
    ) -> None:
        collection = self.client.get_collection(collection_name)
        collection.upsert(
            ids=[p.id for p in points],
            embeddings=[p.vector for p in points],
            metadatas=[p.payload for p in points],
        )

    async def query(
        self, collection_name: str, vector: list[float], top_k: int
    ) -> list[VectorPoint]:
        collection = self.client.get_collection(collection_name)
        results = collection.query(query_embeddings=[vector], n_results=top_k)
        points: list[VectorPoint] = []
        if results.get("ids") and results["ids"][0]:
            for i, pid in enumerate(results["ids"][0]):
                points.append(
                    VectorPoint(
                        id=pid,
                        vector=results["embeddings"][0][i]
                        if results.get("embeddings") and results["embeddings"][0]
                        else [],
                        payload=results["metadatas"][0][i]
                        if results.get("metadatas") and results["metadatas"][0]
                        else {},
                    )
                )
        return points

    async def delete_by_document(
        self, collection_name: str, document_id: str
    ) -> None:
        collection = self.client.get_collection(collection_name)
        collection.delete(where={"document_id": document_id})
