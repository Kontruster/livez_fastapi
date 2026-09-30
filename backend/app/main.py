from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from app.routers import posts_django
from app.routers.auth_users import router as auth_users_router


async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="livej_fastAPI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_users_router)
app.include_router(posts_django.router)

add_pagination(app)