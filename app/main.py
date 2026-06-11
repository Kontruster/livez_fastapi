from fastapi import FastAPI
from fastapi_pagination import add_pagination 
from app.routers import posts_django, groups, comments
from app.routers.auth_users import router as auth_users_router

async def lifespan(app: FastAPI):
    # какой-то код, выполнится до старта приложения
    yield
    # этот код выполнится после завершения

app = FastAPI(title="livej_fastAPI", lifespan=lifespan)
# app.include_router(posts.router)
app.include_router(auth_users_router)
app.include_router(posts_django.router)
app.include_router(groups.router)
app.include_router(comments.router)

add_pagination(app)