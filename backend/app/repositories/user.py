from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Follow, Post, User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return await self.session.scalar(stmt)

    async def get_posts_by_author(self, author_id: int) -> Page:
        stmt = (
            select(Post)
            .where(Post.author_id == author_id)
            .options(
                joinedload(Post.author),
                selectinload(Post.images),
            )
            .order_by(desc(Post.pub_date))
        )
        return await paginate(self.session, stmt, params=Params(page=1, size=50))

    async def count_posts_by_author(self, author_id: int) -> int:
        stmt = select(func.count(Post.id)).where(Post.author_id == author_id)
        return await self.session.scalar(stmt) or 0

    async def is_following(self, user_id: int, author_id: int) -> bool:
        stmt = select(Follow.id).where(Follow.user_id == user_id, Follow.author_id == author_id)
        return (await self.session.scalar(stmt)) is not None

    async def add_follow(self, user_id: int, author_id: int) -> None:
        self.session.add(Follow(user_id=user_id, author_id=author_id))
        await self.session.commit()

    async def remove_follow(self, user_id: int, author_id: int) -> None:
        await self.session.execute(
            delete(Follow).where(Follow.user_id == user_id, Follow.author_id == author_id)
        )
        await self.session.commit()