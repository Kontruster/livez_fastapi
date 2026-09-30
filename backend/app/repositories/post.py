from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Comment, Group, Post, User


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feed(self, q: str | None) -> Page:
        stmt = (
            select(Post)
            .options(joinedload(Post.author))
            .order_by(desc(Post.pub_date))
        )
        if q:
            stmt = stmt.where(Post.text.ilike(f"%{q}%"))
        return await paginate(self.session, stmt)

    async def get_follow_feed(self, user_id: int) -> Page:
        from app.models import Follow
        stmt = (
            select(Post)
            .join(Follow, Post.author_id == Follow.author_id)
            .where(Follow.user_id == user_id)
            .options(joinedload(Post.author))
            .order_by(desc(Post.pub_date))
        )
        return await paginate(self.session, stmt)

    async def get_group_posts(self, group_id: int) -> Page:
        stmt = (
            select(Post)
            .where(Post.group_id == group_id)
            .options(joinedload(Post.author))
            .order_by(desc(Post.pub_date))
        )
        return await paginate(self.session, stmt, params=Params(page=1, size=10))

    async def create(self, author_id, text, image, group_id) -> Post:
        post = Post(text=text, image=image, group_id=group_id, author_id=author_id)
        self.session.add(post)
        await self.session.commit()
        stmt = (
            select(Post)
            .options(joinedload(Post.author))
            .where(Post.id == post.id)
        )
        return await self.session.scalar(stmt)

    async def get_by_id(self, post_id: int) -> Post | None:
        stmt = select(Post).where(Post.id == post_id)
        return await self.session.scalar(stmt)

    async def get_detail_by_id(self, post_id: int) -> Post | None:
        stmt = (
            select(Post)
            .options(
                joinedload(Post.author),
                joinedload(Post.group),
                selectinload(Post.comments).options(joinedload(Comment.author)),
            )
            .where(Post.id == post_id)
        )
        return await self.session.scalar(stmt)

    async def update(self, post: Post, update_data: dict) -> Post:
        for field, value in update_data.items():
            setattr(post, field, value)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def delete(self, post: Post) -> None:
        await self.session.delete(post)
        await self.session.commit()

    async def get_author_post_count(self, author_id: int) -> int:
        stmt = select(func.count(Post.id)).where(Post.author_id == author_id)
        return await self.session.scalar(stmt) or 0

    async def add_comment(self, post_id, author_id, text) -> Comment:
        comment = Comment(text=text, post_id=post_id, author_id=author_id)
        self.session.add(comment)
        await self.session.commit()
        stmt = (
            select(Comment)
            .options(joinedload(Comment.author))
            .where(Comment.id == comment.id)
        )
        return await self.session.scalar(stmt)