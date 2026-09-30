import os
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (AuthenticationBackend,
                                          BearerTransport, CookieTransport,
                                          JWTStrategy)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import engine, get_db
from app.models import User

# from dotenv import load_dotenv


# SECRET_KEY = os.getenv("SECRET_KEY")
SECRET_KEY = settings.SECRET_KEY


# ==================== 1. ТРАНСПОРТ ====================
# Где клиент будет передавать токен? В заголовке Authorization: Bearer <token>
bearer_transport = BearerTransport(tokenUrl="/auth/jwt/login")

# ==================== 2. СТРАТЕГИЯ ====================
# Как создавать, проверять и декодировать токен?
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET_KEY, lifetime_seconds=3600)  # 1 час

# ==================== 3. БЭКЕНД АУТЕНТИФИКАЦИИ ====================
# Связка: ГДЕ искать токен + КАК его проверять
cookie_transport = CookieTransport(
    cookie_name="fastapiusersauth", 
    cookie_max_age=3600,
    cookie_samesite="lax" # 'lax' отлично работает для localhost
)

auth_backend = AuthenticationBackend(
    name="jwt",
    # transport=bearer_transport,
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# ==================== 4. МЕНЕДЖЕР ПОЛЬЗОВАТЕЛЕЙ ====================
# Кастомная бизнес-логика (хуки, валидация, отправка писем)
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    # Секреты для генерации токенов сброса пароля и подтверждения email
    reset_password_token_secret = SECRET_KEY
    verification_token_secret = SECRET_KEY

    # Хук: срабатывает после успешной регистрации
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"Новый пользователь: {user.email} (ID: {user.id})")
        # Здесь можно вызвать send_email(user.email, "Добро пожаловать!")

    # Хук: срабатывает при запросе сброса пароля
    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        print(f"🔑 Токен сброса для {user.email}: {token}")
        # Здесь генерируется ссылка вида /auth/reset-password?token=...

# ==================== 5. ЗАВИСИМОСТИ (DI) ====================
# Адаптер БД для fastapi-users
async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)

# Фабрика менеджера
async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

# Главный объект: даёт доступ ко всем роутам и зависимостям
fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])

# Готовая зависимость для защищённых эндпоинтов
current_active_user = fastapi_users.current_user(active=True)