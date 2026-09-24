from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,           # Максимальное количество постоянных соединений
    max_overflow=20,        # Дополнительные соединения при пиковой нагрузке
    pool_pre_ping=True,     # Проверка соединения перед использованием
    pool_recycle=1800,      # Пересоздавать соединения каждые 30 минут
    echo=False,             # Установите True для отладки SQL-запросов
)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise