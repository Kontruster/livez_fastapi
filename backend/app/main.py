import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination

from app.config import settings
from app.handlers import register_exception_handlers
from app.logging_config import setup_logging
from app.routers import account, posts_django, uploads
from app.routers.auth_users import router as auth_users_router

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.avatars_dir.mkdir(parents=True, exist_ok=True)
    settings.post_images_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "%s запущен. uploads=%s, debug=%s",
        settings.PROJECT_NAME,
        settings.UPLOAD_DIR,
        settings.DEBUG,
    )
    yield
    logger.info("%s остановлен", settings.PROJECT_NAME)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

register_exception_handlers(app)

# ВАЖЕН ПОРЯДОК: account.router объявляет DELETE /users/me и PATCH /users/me/profile.
# fastapi-users в своём /users-роутере регистрирует DELETE /users/{id}, который
# перехватил бы /users/me и вернул 403. Поэтому собственные маршруты аккаунта
# подключаются раньше.
app.include_router(account.router)
app.include_router(auth_users_router)
app.include_router(posts_django.router)
app.include_router(uploads.router)


@app.get("/health", tags=["service"])
async def health():
    """Проверка живости для docker healthcheck и балансировщика."""
    from sqlalchemy import text

    from app.database import async_session_maker

    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Healthcheck: БД недоступна")
        return {"status": "degraded", "database": "down"}
    return {"status": "ok", "database": "up"}


# Размер страницы по умолчанию — 10, максимум 100.
# Клиент задаёт ?page=&size=, эндпоинты принимают их через Depends(Params),
# который подставляется в роутерах (PaginationParams).
add_pagination(app)
