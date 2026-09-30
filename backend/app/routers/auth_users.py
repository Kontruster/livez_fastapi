from fastapi import APIRouter

from app.core.auth import auth_backend, fastapi_users
from app.models import User
from app.schemas import UserCreate, UserRead

router = APIRouter()

# Эндпоинты аутентификации
router.include_router(
    fastapi_users.get_auth_router(auth_backend),  # /auth/jwt/login, /logout
    prefix="/auth/jwt",
    tags=["auth"]
)

# Регистрация
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

# Сброс пароля
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"]
)

# Управление пользователями
router.include_router(
    fastapi_users.get_users_router(UserRead, UserCreate),  # /users/me, /users/{id}
    prefix="/users",
    tags=["users"]
)