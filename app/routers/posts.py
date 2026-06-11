from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Post
# from app.schemas import PostCreate, PostRead
from app.dependencies import get_current_user

router = APIRouter(prefix="/posts/", tags=["posts"])

@router.get("/", response_model=list[PostRead])
async def list_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Post).order_by(Post.pub_date.desc()).offset(skip).limit(limit)
    )   
    return result.scalars().all()

@router.post("/", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # service = PostService(db)
    # service.create_post(post_data)
    db_post = Post(**post_data.model_dump(), author_id=current_user["id"])
    db.add(db_post)
    await db.commit()
    await db.refresh(db_post)
    return db_post

@router.get("/{post_id}", response_model=PostRead)
async def get_post(post_id: int, db: AsyncSession = Depends(get_db)):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Forbidden")
    await db.delete(post)
    await db.commit()