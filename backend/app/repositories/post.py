from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Comment, Follow, Group, GroupMember, Post, PostImage, PostLike
from app.utils.files import try_delete_local_file

# Общие опции загрузки связей для ленты (борьба с N+1)
FEED_OPTIONS = (
    joinedload(Post.author),
    joinedload(Post.group),
    selectinload(Post.images),
)


def _visible_posts_condition(viewer_id: int | None):
    """Пост виден, если он вне групп, в публичной группе или в приватной группе,
    где зритель — участник."""
    public_group = exists(
        select(Group.id).where(Group.id == Post.group_id, Group.is_private.is_(False))
    )
    conds = [Post.group_id.is_(None), public_group]
    if viewer_id is not None:
        membership = exists(
            select(GroupMember.group_id).where(
                GroupMember.group_id == Post.group_id,
                GroupMember.user_id == viewer_id,
            )
        )
        conds.append(membership)
    return or_(*conds)


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_feed(
        self,
        q: str | None = None,
        group_id: int | None = None,
        params: Params | None = None,
        viewer_id: int | None = None,
    ) -> Page:
        stmt = select(Post).options(*FEED_OPTIONS).order_by(Post.pub_date.desc(), Post.id.desc())
        stmt = stmt.where(_visible_posts_condition(viewer_id))
        if q:
            pattern = f"%{q.strip()}%"
            stmt = stmt.where(Post.text.ilike(pattern))
        if group_id is not None:
            stmt = stmt.where(Post.group_id == group_id)
        return await paginate(self.session, stmt, params=params)

    async def get_follow_feed(self, user_id: int, params: Params | None = None) -> Page:
        stmt = (
            select(Post)
            .join(Follow, Post.author_id == Follow.author_id)
            .where(Follow.user_id == user_id)
            .where(_visible_posts_condition(user_id))
            .options(*FEED_OPTIONS)
            .order_by(Post.pub_date.desc(), Post.id.desc())
        )
        return await paginate(self.session, stmt, params=params)

    async def get_group_posts(self, group_id: int, params: Params | None = None) -> Page:
        stmt = (
            select(Post)
            .where(Post.group_id == group_id)
            .options(*FEED_OPTIONS)
            .order_by(Post.pub_date.desc(), Post.id.desc())
        )
        return await paginate(self.session, stmt, params=params)

    async def get_posts_by_author(
        self, author_id: int, params: Params | None = None, viewer_id: int | None = None
    ) -> Page:
        stmt = (
            select(Post)
            .where(Post.author_id == author_id)
            .where(_visible_posts_condition(viewer_id))
            .options(*FEED_OPTIONS)
            .order_by(Post.pub_date.desc(), Post.id.desc())
        )
        return await paginate(self.session, stmt, params=params)

    async def create(
        self,
        author_id: int,
        text: str,
        image: str | None = None,
        group_id: int | None = None,
    ) -> Post:
        post = Post(text=text, image=image, group_id=group_id, author_id=author_id)
        self.session.add(post)
        await self.session.flush()
        return post

    async def get_by_id(self, post_id: int) -> Post | None:
        stmt = select(Post).options(*FEED_OPTIONS).where(Post.id == post_id)
        return await self.session.scalar(stmt)

    async def get_detail_by_id(self, post_id: int) -> Post | None:
        stmt = (
            select(Post)
            .options(
                joinedload(Post.author),
                joinedload(Post.group),
                selectinload(Post.comments).options(joinedload(Comment.author)),
                selectinload(Post.images),
            )
            .where(Post.id == post_id)
        )
        return await self.session.scalar(stmt)

    async def update(self, post: Post, update_data: dict) -> Post:
        if "image" in update_data and update_data["image"] != post.image:
            try_delete_local_file(post.image)

        for field, value in update_data.items():
            setattr(post, field, value)
        await self.session.flush()
        await self.session.refresh(post)
        return post

    async def delete(self, post: Post) -> None:
        try_delete_local_file(post.image)
        for img in list(post.images or []):
            try_delete_local_file(img.url)

        await self.session.delete(post)
        await self.session.flush()

    async def get_author_post_count(self, author_id: int) -> int:
        stmt = select(func.count(Post.id)).where(Post.author_id == author_id)
        return await self.session.scalar(stmt) or 0

    # ---------- Комментарии ----------

    async def add_comment(
        self,
        post_id: int,
        author_id: int,
        text: str,
        parent_id: int | None = None,
    ) -> Comment:
        comment = Comment(text=text, post_id=post_id, author_id=author_id, parent_id=parent_id)
        self.session.add(comment)
        await self.session.flush()
        stmt = select(Comment).options(joinedload(Comment.author)).where(Comment.id == comment.id)
        return await self.session.scalar(stmt)

    async def get_comment(self, comment_id: int) -> Comment | None:
        stmt = select(Comment).options(joinedload(Comment.author)).where(Comment.id == comment_id)
        return await self.session.scalar(stmt)

    async def delete_comment(self, comment: Comment) -> None:
        await self.session.delete(comment)
        await self.session.flush()

    # ---------- Лайки ----------

    async def add_like(self, post_id: int, user_id: int) -> None:
        exists_stmt = select(PostLike.id).where(
            PostLike.post_id == post_id, PostLike.user_id == user_id
        )
        if (await self.session.scalar(exists_stmt)) is None:
            self.session.add(PostLike(post_id=post_id, user_id=user_id))
            await self.session.flush()

    async def remove_like(self, post_id: int, user_id: int) -> None:
        await self.session.execute(
            delete(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
        )
        await self.session.flush()

    async def is_liked(self, post_id: int, user_id: int) -> bool:
        stmt = select(PostLike.id).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
        return (await self.session.scalar(stmt)) is not None

    async def count_likes(self, post_id: int) -> int:
        stmt = select(func.count(PostLike.id)).where(PostLike.post_id == post_id)
        return await self.session.scalar(stmt) or 0

    async def set_images(self, post_id: int, urls: list[str]) -> None:
        """Заменяет набор картинок поста, удаляя файлы, выпавшие из набора."""
        stmt = select(PostImage).where(PostImage.post_id == post_id)
        old = (await self.session.scalars(stmt)).all()
        old_urls = {img.url for img in old}
        new_urls = list(urls)

        for img in old:
            await self.session.delete(img)

        await self.session.flush()

        for i, url in enumerate(new_urls):
            self.session.add(PostImage(post_id=post_id, url=url, position=i))

        await self.session.flush()

        for url in old_urls - set(new_urls):
            try_delete_local_file(url)
