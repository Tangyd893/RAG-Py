"""add performance indexes

Revision ID: e62e7423c9f3
Revises: 067ddcf6345a
Create Date: 2026-05-28 03:02:31.387446
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e62e7423c9f3'
down_revision: Union[str, None] = '067ddcf6345a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级到当前 revision。"""
    op.create_index(
        "idx_knowledge_bases_owner", "knowledge_bases", ["owner_id"]
    )
    op.create_index(
        "idx_documents_kb_status", "documents", ["knowledge_base_id", "status"]
    )
    op.create_index(
        "idx_documents_created_at",
        "documents",
        [sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_chunks_document", "chunks", ["document_id", "chunk_index"]
    )
    op.create_index(
        "idx_chunks_kb", "chunks", ["knowledge_base_id"]
    )
    op.create_index(
        "idx_indexing_jobs_document", "indexing_jobs", ["document_id"]
    )
    op.create_index(
        "idx_query_logs_kb_created",
        "query_logs",
        ["knowledge_base_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_query_logs_user_created",
        "query_logs",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    """回滚到上一个 revision。"""
    op.drop_index("idx_query_logs_user_created", table_name="query_logs")
    op.drop_index("idx_query_logs_kb_created", table_name="query_logs")
    op.drop_index("idx_indexing_jobs_document", table_name="indexing_jobs")
    op.drop_index("idx_chunks_kb", table_name="chunks")
    op.drop_index("idx_chunks_document", table_name="chunks")
    op.drop_index("idx_documents_created_at", table_name="documents")
    op.drop_index("idx_documents_kb_status", table_name="documents")
    op.drop_index("idx_knowledge_bases_owner", table_name="knowledge_bases")
