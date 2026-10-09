from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Follow, Post, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(func.lower(User.username) == username.lower())
        return await self.session.scalar(stmt)

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def username_exists(self, username: str, exclude_id: int | None = None) -> bool:
        stmt = select(User.id).where(func.lower(User.username) == username.lower())
        if exclude_id is not None:
            stmt = stmt.where(User.id != exclude_id)
        return (await self.session.scalar(stmt)) is not None

    async def get_posts_by_author(
        self, author_id: int, params: Params | None = None, viewer_id: int | None = None
    ) -> Page:
        from app.repositories.post import _visible_posts_condition

        stmt = (
            select(Post)
            .where(Post.author_id == author_id)
            .where(_visible_posts_condition(viewer_id))
            .options(
                joinedload(Post.author),
                joinedload(Post.group),
                selectinload(Post.images),
            )
            .order_by(Post.pub_date.desc(), Post.id.desc())
        )
        return await paginate(self.session, stmt, params=params)

    async def count_posts_by_author(self, author_id: int) -> int:
        stmt = select(func.count(Post.id)).where(Post.author_id == author_id)
        return await self.session.scalar(stmt) or 0

    async def count_followers(self, author_id: int) -> int:
        stmt = select(func.count(Follow.id)).where(Follow.author_id == author_id)
        return await self.session.scalar(stmt) or 0

    async def count_following(self, user_id: int) -> int:
        stmt = select(func.count(Follow.id)).where(Follow.user_id == user_id)
        return await self.session.scalar(stmt) or 0

    async def is_following(self, user_id: int, author_id: int) -> bool:
        stmt = select(Follow.id).where(Follow.user_id == user_id, Follow.author_id == author_id)
        return (await self.session.scalar(stmt)) is not None

    async def add_follow(self, user_id: int, author_id: int) -> None:
        self.session.add(Follow(user_id=user_id, author_id=author_id))
        await self.session.flush()

    async def remove_follow(self, user_id: int, author_id: int) -> None:
        await self.session.execute(
            delete(Follow).where(Follow.user_id == user_id, Follow.author_id == author_id)
        )
        await self.session.flush()
