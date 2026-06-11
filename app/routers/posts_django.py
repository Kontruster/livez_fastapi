from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select, func, delete, desc
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession #
from typing import Optional

from app.database import get_db
from app.models import Post, User, Group, Comment, Follow
from app.schemas import *
# from app.dependencies import get_current_user
from app.core.auth import current_active_user

router = APIRouter(tags=["posts"])


@router.get("/posts/", response_model=Page[PostList])
async def index(
    q: Optional[str] = Query(None, description="Поиск по тексту"),
    db: AsyncSession = Depends(get_db)
):
    # joinedload тянет автора сразу
    stmt = (
        select(Post)
        .options(joinedload(Post.author).load_only(User.id, User.username))
        .order_by(desc(Post.pub_date))
    )
    if q:
        stmt = stmt.where(Post.text.ilike(f"%{q}%"))
        
    return await paginate(db, stmt)


@router.get("/follow/", response_model=Page[PostList])
async def follow_index(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    stmt = (
        select(Post)
        .join(Follow, Post.author_id == Follow.author_id)
        .where(Follow.user_id == current_user.id)
        .options(joinedload(Post.author).load_only(User.id, User.username)) # не все поля
        .order_by(desc(Post.pub_date))
    )
    return await paginate(db, stmt)


@router.get("/groups/{slug}/")
async def group_posts(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    group = await db.scalar(select(Group).where(Group.slug == slug))
    if not group:
        raise HTTPException(404, "Сообщество не найдено")

    stmt = (
        select(Post)
        .where(Post.group_id == group.id)
        .order_by(desc(Post.pub_date))
    )
    posts_page = await paginate(db, stmt)
    
    # Возвращаем группу + пагинированные посты
    return {"group": group, "posts": posts_page}


@router.post("/posts/", response_model=PostList, status_code=201)
async def create_post(
    form: PostCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(current_active_user)
    current_user: User = Depends(current_active_user) # добавлено
):
    new_post = Post(
        text=form.text,
        image=form.image,
        group_id=form.group_id,  # Если None → запишется NULL
        # author_id=current_user.get("id")
        author_id=current_user.id
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)  # Подтягиваем id и pub_date из БД
    return new_post


@router.patch("/posts/{post_id}/", response_model=PostList)
async def edit_post(
    post_id: int,
    form: PostCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(current_active_user)
    current_user: User = Depends(current_active_user)
):
    post = await db.scalar(select(Post).where(Post.id == post_id))
    if not post:
        raise HTTPException(404, "Пост не найден")
    if post.author_id != current_user.id:
        raise HTTPException(403, "Только автор может редактировать пост")

    # Обновляем только переданные поля
    for field, value in form.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
        
    await db.commit()
    await db.refresh(post)
    return post


async def _get_profile_logic(db, target_username, current_user):
    author = await db.scalar(select(User).where(User.username == target_username))
    if not author:
        raise HTTPException(404, "Пользователь не найден")

    # Пагинация постов автора
    stmt = select(Post).where(Post.author_id == author.id).order_by(desc(Post.pub_date))
    posts_page = await paginate(db, stmt)

    total_posts = await db.scalar(
        select(func.count(Post.id)).where(Post.author_id == author.id)
    )

    # Проверка подписки
    is_following = False
    if current_user and current_user.id != author.id:
        exists = await db.scalar(
            select(Follow.id).where(
                Follow.user_id == current_user.id, 
                Follow.author_id == author.id
            ) # None, 6
        )
        is_following = exists is not None

    return {
        "author": author,
        "posts": posts_page,
        "is_following": is_following,
        "total_posts": total_posts
    }

@router.get("/profile/me", response_model=ProfileResponse)
async def my_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    return await _get_profile_logic(db, current_user.username, current_user)

@router.get("/profile/{username}", response_model=ProfileResponse)
async def user_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(current_active_user)
):
    return await _get_profile_logic(db, username, current_user)


@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def post_detail(post_id: int, db: AsyncSession = Depends(get_db)):
    # 1 запрос: Post + Author + Group + Comments (без N+1)
    stmt = (
        select(Post)
        .options(
            joinedload(Post.author).load_only(User.id, User.username),
            joinedload(Post.group),
            selectinload(Post.comments).options(joinedload(Comment.author).load_only(User.id, User.username))
        )
        .where(Post.id == post_id)
    )
    post = await db.scalar(stmt)
    if not post:
        raise HTTPException(404, "Пост не найден")

    # Отдельный быстрый запрос на count
    author_post_count = await db.scalar(
        select(func.count(Post.id)).where(Post.author_id == post.author_id)
    )

    return PostDetailResponse(post=post, author_post_count=author_post_count)


@router.get("/groups/", response_model=list[GroupRead])
async def list_groups(db: AsyncSession = Depends(get_db)):
    stmt = select(Group).order_by(Group.title)
    return await db.scalars(stmt).all()


@router.post("/posts/{post_id}/comments/", response_model=CommentRead, status_code=201)
async def add_comment(
    post_id: int,
    form: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    post = await db.scalar(select(Post).where(Post.id == post_id))
    if not post:
        raise HTTPException(404, "Пост не найден")

    comment = Comment(text=form.text, post_id=post_id, author_id=current_user.id)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


@router.post("/profile/{username}/follow/", status_code=201)
async def follow_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    author = await db.scalar(select(User).where(User.username == username))
    if not author or author.id == current_user.id:
        raise HTTPException(400, "Нельзя подписаться на себя или несуществующего пользователя")

    exists = await db.scalar(
        select(Follow).where(Follow.user_id == current_user.id, Follow.author_id == author.id)
    )
    if not exists:
        db.add(Follow(user_id=current_user.id, author_id=author.id))
        await db.commit()
    return {"status": "following"}


@router.delete("/profile/{username}/follow/")
async def unfollow_user(
    username: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    author = await db.scalar(select(User).where(User.username == username))
    if not author:
        raise HTTPException(404, "Пользователь не найден")

    await db.execute(
        delete(Follow).where(Follow.user_id == current_user.id, Follow.author_id == author.id)
    )
    await db.commit()
    return {"status": "unfollowed"}


@router.delete("/posts/{post_id}/", status_code=204)
async def delete_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    # Достать пост из базы
    # проверка на None
    # проверка автора поста
    # .execute для delete
    post = await db.scalar(select(Post).where(Post.id == post_id))
    if not post:
        raise HTTPException(404, "Пост не найден")
    
    if current_user.id != post.author_id:
        raise HTTPException(403, "Вы можете удалить только свои посты")

    # await db.execute(
    #     delete(Post).where(Post.id == post_id)
    # )
    await db.execute(delete(post))
    await db.commit()
    return {"status": "success"}
