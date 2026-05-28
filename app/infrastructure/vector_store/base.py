"""向量存储抽象接口。"""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class VectorPoint:
    """向量点数据结构。"""
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


class VectorStore(Protocol):
    """向量存储抽象接口——MV用 Chroma，后续可换 Qdrant。"""

    async def ensure_collection(self, name: str, dimension: int) -> None:
        """确保 collection 存在，不存在则创建。"""
        ...

    async def upsert(
        self, collection_name: str, points: list[VectorPoint]
    ) -> None:
        """批量写入或更新向量点。"""
        ...

    async def query(
        self, collection_name: str, vector: list[float], top_k: int
    ) -> list[VectorPoint]:
        """按余弦相似度检索 top_k 个向量点。"""
        ...

    async def delete_by_document(
        self, collection_name: str, document_id: str
    ) -> None:
        """按文档 ID 删除所有关联向量点。"""
        ...
