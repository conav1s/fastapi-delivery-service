from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from delivery_service.config import settings

engine = create_async_engine(settings.postgres.database_url)

session_factory = async_sessionmaker(engine, expire_on_commit=False)
