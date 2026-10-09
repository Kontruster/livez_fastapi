"""Общие фикстуры тестов.

Тесты используют SQLite в памяти (aiosqlite), поэтому не требуют
запущенного PostgreSQL. Схема создаётся из моделей, а не миграциями —
сами миграции проверяются отдельным тестом.
"""

import os
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

# Переменные окружения нужно выставить ДО импорта app.config
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:5173")

import pytest
import pytest_asyncio
from _pytest.tmpdir import TempPathFactory
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def tmp_path_factory(tmp_path_factory):
    """Отдаёт стандартную фабрику временных каталогов pytest.

    Каталог можно переопределить переменной PYTEST_TMP_ROOT. Она нужна там,
    где системный %TEMP% недоступен для записи (например, в некоторых
    контейнерах или песочницах): тогда укажите путь внутри проекта.
    """
    root = os.environ.get("PYTEST_TMP_ROOT")
    if not root:
        return tmp_path_factory

    base = Path(root)
    base.mkdir(parents=True, exist_ok=True)
    return TempPathFactory(base, base.name, 3, None)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # SQLite не применяет ON DELETE CASCADE без этого прагмы.
    from sqlalchemy import event

    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def session_maker(engine):
    return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


@pytest_asyncio.fixture
async def db_session(session_maker) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def client(session_maker) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def user_factory():
    """Генерирует уникальные данные пользователя."""

    def _make(prefix: str = "user") -> dict:
        token = uuid.uuid4().hex[:8]
        return {
            "email": f"{prefix}_{token}@example.com",
            "password": "supersecret123",
            "username": f"{prefix}_{token}",
        }

    return _make


@pytest_asyncio.fixture
async def auth_client(client, user_factory):
    """Клиент, зарегистрированный и залогиненный (cookie в jar)."""
    creds = user_factory("auth")

    resp = await client.post(
        "/auth/register",
        json={
            "email": creds["email"],
            "password": creds["password"],
            "username": creds["username"],
        },
    )
    assert resp.status_code == 201, resp.text

    resp = await client.post(
        "/auth/jwt/login",
        data={"username": creds["email"], "password": creds["password"]},
    )
    assert resp.status_code == 204, resp.text

    me = await client.get("/users/me")
    assert me.status_code == 200, me.text

    return client, me.json()


@pytest_asyncio.fixture
async def anon_client(session_maker) -> AsyncGenerator[AsyncClient, None]:
    """Отдельный клиент без cookie — «анонимный посетитель».

    Нужен потому, что фикстура ``client`` переиспользуется ``auth_client``,
    и после логина её cookie-jar уже авторизован.
    """

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def second_client(session_maker, user_factory):
    """Второй независимый пользователь со своим cookie-jar."""

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        creds = user_factory("second")
        resp = await ac.post(
            "/auth/register",
            json={
                "email": creds["email"],
                "password": creds["password"],
                "username": creds["username"],
            },
        )
        assert resp.status_code == 201, resp.text
        resp = await ac.post(
            "/auth/jwt/login",
            data={"username": creds["email"], "password": creds["password"]},
        )
        assert resp.status_code == 204, resp.text
        yield ac
