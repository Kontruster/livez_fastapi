from collections.abc import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# SQLite (локальная разработка без Docker и тесты) не поддерживает
# pool_size/max_overflow — параметры пула задаются только для PostgreSQL.
_IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")
_IS_MEMORY = ":memory:" in settings.DATABASE_URL or "mode=memory" in settings.DATABASE_URL


def _create_engine():
    kwargs: dict = {"echo": settings.DEBUG, "pool_pre_ping": True}

    if _IS_SQLITE:
        if _IS_MEMORY:
            from sqlalchemy.pool import StaticPool

            # одно общее соединение: иначе схема в памяти «теряется»
            kwargs["poolclass"] = StaticPool
            kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs |= {
            "pool_size": 10,  # Максимальное количество постоянных соединений
            "max_overflow": 20,  # Дополнительные соединения при пиковой нагрузке
            "pool_recycle": 1800,  # Пересоздавать соединения каждые 30 минут
        }

    engine = create_async_engine(settings.DATABASE_URL, **kwargs)

    if _IS_SQLITE:
        # SQLite по умолчанию НЕ применяет FOREIGN KEY ... ON DELETE CASCADE.
        # Без этого прагмы удаление родительской записи оставляет «сирот».
        @event.listens_for(engine.sync_engine, "connect")
        def _enable_sqlite_fk(dbapi_connection, _connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = _create_engine()

async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Одна транзакция на HTTP-запрос.

    Репозитории используют ``flush()``, а не ``commit()``: запрос либо
    фиксируется целиком, либо откатывается целиком при любой ошибке.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
