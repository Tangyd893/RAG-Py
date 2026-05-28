"""通用仓储基类。"""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """通用 CRUD 仓储基类，实体 Repository 继承并添加特化查询。"""

    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get(self, id: UUID) -> T | None:
        return await self.session.get(self.model, id)

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def list_all(self) -> list[T]:
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())


from app.infrastructure.db.models import Document, DocumentStatus, KnowledgeBase  # noqa: E402


class KnowledgeBaseRepository(BaseRepository[KnowledgeBase]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, KnowledgeBase)

    async def list_by_owner(
        self, owner_id: UUID, offset: int = 0, limit: int = 20
    ) -> tuple[list[KnowledgeBase], int]:
        count_q = (
            select(func.count())
            .select_from(KnowledgeBase)
            .where(KnowledgeBase.owner_id == owner_id)
        )
        total = (await self.session.execute(count_q)).scalar_one()

        q = (
            select(KnowledgeBase)
            .where(KnowledgeBase.owner_id == owner_id)
            .order_by(KnowledgeBase.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    async def get_with_stats(self, kb_id: UUID) -> KnowledgeBase | None:
        return await self.session.get(KnowledgeBase, kb_id)


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Document)

    async def get_by_kb_and_checksum(
        self, kb_id: UUID, checksum: str
    ) -> Document | None:
        q = (
            select(Document)
            .where(
                Document.knowledge_base_id == kb_id,
                Document.checksum == checksum,
            )
            .limit(1)
        )
        result = await self.session.execute(q)
        return result.scalar_one_or_none()
