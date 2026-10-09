"""Общая логика сериализации постов в ответы API.

Счётчики комментариев и лайков считаются групповыми запросами на страницу,
а не отдельным запросом на каждый пост. Комментарии собираются в дерево
(ответы вкладываются в родительские).
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment, Post, PostLike
from app.schemas import (
    CommentRead,
    GroupRead,
    PostDetail,
    PostImageRead,
    PostList,
    UserShort,
)


def comment_to_read(comment: Comment, replies: list[CommentRead] | None = None) -> CommentRead:
    """Собирает CommentRead явно, не трогая ленивую связь ``replies``.

    ``model_validate`` обратился бы к ``comment.replies`` и выполнил бы
    ленивую загрузку из async-контекста (MissingGreenlet).
    """
    return CommentRead(
        id=comment.id,
        text=comment.text,
        pub_date=comment.pub_date,
        author=UserShort.model_validate(comment.author),
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        replies=replies or [],
    )


async def comments_count_map(session: AsyncSession, post_ids: Sequence[int]) -> dict[int, int]:
    if not post_ids:
        return {}
    stmt = (
        select(Comment.post_id, func.count(Comment.id))
        .where(Comment.post_id.in_(list(post_ids)))
        .group_by(Comment.post_id)
    )
    rows = await session.execute(stmt)
    return dict(rows.all())


async def likes_count_map(session: AsyncSession, post_ids: Sequence[int]) -> dict[int, int]:
    if not post_ids:
        return {}
    stmt = (
        select(PostLike.post_id, func.count(PostLike.id))
        .where(PostLike.post_id.in_(list(post_ids)))
        .group_by(PostLike.post_id)
    )
    rows = await session.execute(stmt)
    return dict(rows.all())


async def liked_post_ids(
    session: AsyncSession, viewer_id: int | None, post_ids: Sequence[int]
) -> set[int]:
    """Множество id постов, которые лайкнул текущий пользователь."""
    if viewer_id is None or not post_ids:
        return set()
    stmt = select(PostLike.post_id).where(
        PostLike.post_id.in_(list(post_ids)), PostLike.user_id == viewer_id
    )
    rows = await session.execute(stmt)
    return {row[0] for row in rows.all()}


def build_comment_tree(comments: Sequence[Comment]) -> list[CommentRead]:
    """Собирает плоский список комментариев в дерево по parent_id."""
    nodes: dict[int, CommentRead] = {}
    for comment in comments:
        nodes[comment.id] = comment_to_read(comment)

    roots: list[CommentRead] = []
    for comment in comments:
        node = nodes[comment.id]
        if comment.parent_id is not None and comment.parent_id in nodes:
            nodes[comment.parent_id].replies.append(node)
        else:
            roots.append(node)
    return roots


async def serialize_posts(
    session: AsyncSession, posts: Sequence[Post], viewer_id: int | None = None
) -> list[PostList]:
    post_ids = [p.id for p in posts]
    comment_counts = await comments_count_map(session, post_ids)
    like_counts = await likes_count_map(session, post_ids)
    liked = await liked_post_ids(session, viewer_id, post_ids)

    result = []
    for post in posts:
        item = PostList.model_validate(post)
        item.comments_count = comment_counts.get(post.id, 0)
        item.likes_count = like_counts.get(post.id, 0)
        item.is_liked = post.id in liked
        result.append(item)
    return result


async def serialize_post_page(
    session: AsyncSession, page: Any, viewer_id: int | None = None
) -> Any:
    """Пересобирает страницу пагинации, добавляя comments_count и лайки."""
    items = await serialize_posts(session, page.items, viewer_id=viewer_id)
    return page.model_copy(update={"items": items})


async def serialize_post_detail(
    session: AsyncSession, post: Post, viewer_id: int | None = None
) -> PostDetail:
    post_ids = [post.id]
    comment_counts = await comments_count_map(session, post_ids)
    like_counts = await likes_count_map(session, post_ids)
    liked = await liked_post_ids(session, viewer_id, post_ids)

    # CommentRead/PostDetail не собираем через model_validate: он обратился бы
    # к ленивой связи replies у каждого комментария (MissingGreenlet в async).
    detail = PostDetail(
        id=post.id,
        text=post.text,
        pub_date=post.pub_date,
        image=post.image,
        author=UserShort.model_validate(post.author),
        author_id=post.author_id,
        group=GroupRead.model_validate(post.group) if post.group else None,
        comments=build_comment_tree(post.comments),
        images=[PostImageRead.model_validate(img) for img in post.images],
        comments_count=comment_counts.get(post.id, 0),
        likes_count=like_counts.get(post.id, 0),
        is_liked=post.id in liked,
    )
    return detail
