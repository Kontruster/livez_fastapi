from fastapi import FastAPI
from app.routers import posts, groups, comments

async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="livej_fastAPI", lifespan=lifespan)
app.include_router(posts.router)
app.include_router(groups.router)
app.include_router(comments.router)