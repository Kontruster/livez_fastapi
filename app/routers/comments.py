from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Comment, Post
from app.schemas import CommentCreate, CommentRead
from app.dependencies import get_current_user

router = APIRouter(prefix="/posts/{post_id}/comments", tags=["comments"])

@router.get("/", response_model=list[CommentRead])
async def list_comments(post_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Comment).where(Comment.post_id == post_id))
    return result.scalars().all()

@router.post("/", response_model=CommentRead, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    post = await db.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db_comment = Comment(
        **comment_data.model_dump(),
        post_id=post_id,
        author_id=current_user["id"]
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment