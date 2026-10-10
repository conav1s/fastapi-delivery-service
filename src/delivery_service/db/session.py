from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from delivery_service.config import settings

engine = create_async_engine(settings.postgres.database_url)

session_factory = async_sessionmaker(engine, expire_on_commit=False)
