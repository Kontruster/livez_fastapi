import logging

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, CookieTransport, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)

SECRET_KEY = settings.SECRET_KEY
TOKEN_LIFETIME = settings.ACCESS_TOKEN_EXPIRE_SECONDS


# ==================== 1. ТРАНСПОРТ ====================
# Токен передаётся в httpOnly-cookie. Флаг Secure берётся из настроек:
# включать его при работе по HTTP нельзя — браузер не отправит cookie,
# и любой защищённый эндпоинт вернёт 401.
cookie_transport = CookieTransport(
    cookie_name="fastapiusersauth",
    cookie_max_age=TOKEN_LIFETIME,
    cookie_samesite=settings.COOKIE_SAMESITE,
    cookie_httponly=True,
    cookie_secure=settings.COOKIE_SECURE,
)

# ==================== 2. СТРАТЕГИЯ ====================


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=SECRET_KEY,
        lifetime_seconds=TOKEN_LIFETIME,
        algorithm=settings.ALGORITHM,
    )


# ==================== 3. БЭКЕНД АУТЕНТИФИКАЦИИ ====================
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


# ==================== 4. МЕНЕДЖЕР ПОЛЬЗОВАТЕЛЕЙ ====================
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET_KEY
    verification_token_secret = SECRET_KEY

    async def on_after_register(self, user: User, request: Request | None = None):
        logger.info("Новый пользователь: %s (ID: %s)", user.email, user.id)

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        # В проде здесь отправка письма. Токен в логи не пишем.
        logger.info("Запрошен сброс пароля для пользователя ID %s", user.id)

    async def on_after_request_verify(self, user: User, token: str, request: Request | None = None):
        logger.info("Запрошено подтверждение email для пользователя ID %s", user.id)

    async def validate_password(self, password: str, user: User) -> None:
        from fastapi import HTTPException

        if len(password) < 8:
            raise HTTPException(
                status_code=400, detail="Пароль должен содержать минимум 8 символов"
            )
        await super().validate_password(password, user)


# ==================== 5. ЗАВИСИМОСТИ (DI) ====================
async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_optional_user = fastapi_users.current_user(active=True, optional=True)
