from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.config import settings
from app.routers import posts_django
from app.routers.auth_users import router as auth_users_router

from pathlib import Path
from fastapi.staticfiles import StaticFiles
from app.routers import account, uploads

Path("uploads/avatars").mkdir(parents=True, exist_ok=True)
Path("uploads/posts").mkdir(parents=True, exist_ok=True)


async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="livej_fastAPI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth_users_router)
app.include_router(posts_django.router)
app.include_router(account.router)
app.include_router(uploads.router)

add_pagination(app)