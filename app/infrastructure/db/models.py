"""RAG-Py 核心数据模型（7 张表）。

严格按照 docs/RAG系统项目架构设计文档.md 第 4.3 节定义。
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CHAR,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.base import Base, TimestampMixin


# ── 枚举 ─────────────────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    admin = "admin"
    user = "user"


class UserStatus(str, enum.Enum):
    active = "active"
    disabled = "disabled"


class KBStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    parsing = "parsing"
    chunking = "chunking"
    embedding = "embedding"
    indexed = "indexed"
    failed = "failed"
    deleting = "deleting"
    deleted = "deleted"


class JobStatus(str, enum.Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class QueryStatusEnum(str, enum.Enum):
    succeeded = "succeeded"
    failed = "failed"


# ── 模型 ──────────────────────────────────────────────────────────────


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[UserRole] = mapped_column(
        String(32), default=UserRole.user, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        String(32), default=UserStatus.active, nullable=False
    )

    # 关联
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        back_populates="owner", lazy="selectin"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="uploader", lazy="selectin"
    )
    query_logs: Mapped[list["QueryLog"]] = relationship(
        back_populates="user", lazy="selectin"
    )


class KnowledgeBase(Base, TimestampMixin):
    __tablename__ = "knowledge_bases"
    __table_args__ = (UniqueConstraint("vector_collection"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    vector_collection: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    chunk_size: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    chunk_overlap: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    retrieval_top_k: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    rerank_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[KBStatus] = mapped_column(
        String(32), default=KBStatus.active, nullable=False
    )

    # 关联
    owner: Mapped["User"] = relationship(back_populates="knowledge_bases")
    documents: Mapped[list["Document"]] = relationship(
        back_populates="knowledge_base", lazy="selectin"
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="knowledge_base", lazy="selectin"
    )
    query_logs: Mapped[list["QueryLog"]] = relationship(
        back_populates="knowledge_base", lazy="selectin"
    )


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("knowledge_base_id", "checksum"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id"), nullable=False
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    parser_name: Mapped[Optional[str]] = mapped_column(String(128))
    page_count: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[DocumentStatus] = mapped_column(
        String(32), default=DocumentStatus.uploaded, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # 关联
    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="documents")
    uploader: Mapped["User"] = relationship(back_populates="documents")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", lazy="selectin", cascade="all, delete-orphan"
    )
    indexing_jobs: Mapped[list["IndexingJob"]] = relationship(
        back_populates="document", lazy="selectin", cascade="all, delete-orphan"
    )


class Chunk(Base, TimestampMixin):
    __tablename__ = "chunks"
    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index"),
        UniqueConstraint("vector_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    start_offset: Mapped[Optional[int]] = mapped_column(Integer)
    end_offset: Mapped[Optional[int]] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )
    vector_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    # 关联
    document: Mapped["Document"] = relationship(back_populates="chunks")
    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="chunks")
    query_sources: Mapped[list["QuerySource"]] = relationship(
        back_populates="chunk", lazy="selectin"
    )


class IndexingJob(Base):
    __tablename__ = "indexing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    task_id: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[JobStatus] = mapped_column(
        String(32), default=JobStatus.queued, nullable=False
    )
    attempt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(String(128))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关联
    document: Mapped["Document"] = relationship(back_populates="indexing_jobs")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    knowledge_base_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_bases.id"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_queries: Mapped[dict] = mapped_column(
        JSON, default=list, nullable=False
    )
    answer: Mapped[Optional[str]] = mapped_column(Text)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    retrieval_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    generation_latency_ms: Mapped[Optional[int]] = mapped_column(Integer)
    model_name: Mapped[Optional[str]] = mapped_column(String(128))
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[QueryStatusEnum] = mapped_column(
        String(32), default=QueryStatusEnum.succeeded, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # 关联
    user: Mapped["User"] = relationship(back_populates="query_logs")
    knowledge_base: Mapped["KnowledgeBase"] = relationship(back_populates="query_logs")
    sources: Mapped[list["QuerySource"]] = relationship(
        back_populates="query_log", lazy="selectin", cascade="all, delete-orphan"
    )


class QuerySource(Base):
    __tablename__ = "query_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    query_log_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("query_logs.id", ondelete="CASCADE"), nullable=False
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("chunks.id")
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("documents.id")
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Double, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # 关联
    query_log: Mapped["QueryLog"] = relationship(back_populates="sources")
    chunk: Mapped[Optional["Chunk"]] = relationship(back_populates="query_sources")
    document: Mapped[Optional["Document"]] = relationship()
