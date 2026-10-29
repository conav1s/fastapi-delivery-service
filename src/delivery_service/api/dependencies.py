from collections.abc import AsyncGenerator
from typing import Annotated
import uuid

from fastapi import Cookie, Depends, Request, Response
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from delivery_service.config import settings
from delivery_service.db.session import session_factory
from delivery_service.services.packages import PackageService
from delivery_service.services.support import SupportService


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with session_factory() as session:
        yield session


async def get_package_service(
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> PackageService:
    return PackageService(db)


def get_support_service(request: Request) -> SupportService:
    service: SupportService = request.app.state.support_service
    return service


def _parse_session_id(raw: str | None) -> uuid.UUID | None:
    if raw is None:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        # A cookie the client mangled or a stale format: treat it as no session at all.
        # Typed as UUID, it would fail validation with 422 on every request until the
        # user cleared cookies by hand.
        logger.info("Invalid session cookie, issuing a new session")
        return None


async def get_user_session_id(
    response: Response,
    raw_session_id: Annotated[
        str | None, Cookie(alias=settings.session.name, include_in_schema=False)
    ] = None,
) -> uuid.UUID:
    session_id = _parse_session_id(raw_session_id)
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
