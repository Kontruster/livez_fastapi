from fastapi import FastAPI
from fastapi_pagination import add_pagination 
from app.routers import posts_django
from app.routers.auth_users import router as auth_users_router
from fastapi.middleware.cors import CORSMiddleware

async def lifespan(app: FastAPI):
    yield

# Создаем приложение ОДИН раз
app = FastAPI(title="livej_fastAPI", lifespan=lifespan)

# Добавляем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True, # ОБЯЗАТЕЛЬНО для CookieTransport
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth_users_router)
app.include_router(posts_django.router)

add_pagination(app)