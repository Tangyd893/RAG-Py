"""FastAPI 依赖注入：会话、鉴权、分页。"""

from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.db.models import User
from app.infrastructure.db.session import get_session  # noqa: F401
from app.schemas.common import PaginationParams

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """开发模式鉴权：通过 DEV_AUTH_TOKEN 校验，自动创建默认用户。"""
    if not settings.dev_auth_token:
        return None
    if not credentials or credentials.credentials != settings.dev_auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="UNAUTHORIZED",
        )
    result = await session.execute(
        select(User).where(User.email == "dev@rag.local").limit(1)
    )
    user = result.scalar_one_or_none()
    if not user:
        user = User(email="dev@rag.local")
        session.add(user)
        await session.flush()
    return user


async def get_pagination(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)
