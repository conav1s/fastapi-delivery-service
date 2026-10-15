from collections.abc import AsyncGenerator
from typing import Annotated
import uuid

from fastapi import Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from delivery_service.config import settings
from delivery_service.db.session import session_factory
from delivery_service.services.packages import PackageService


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def get_package_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PackageService:
    return PackageService(db)


async def get_user_session_id(
    response: Response,
    session_id: Annotated[
        uuid.UUID | None, Cookie(alias=settings.session.name, include_in_schema=False)
    ] = None,
) -> uuid.UUID:
    if session_id is None:
        session_id = uuid.uuid4()

        response.set_cookie(
            key=settings.session.name,
            value=str(session_id),
            httponly=settings.session.httponly,
            secure=settings.session.secure,
            samesite=settings.session.samesite,
            max_age=settings.session.max_age,
        )

    return session_id
