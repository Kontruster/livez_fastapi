from fastapi_pagination import Page, Params

from app.exceptions import (
    CommentNotFoundError,
    GroupNotFoundError,
    NotGroupMemberError,
    PermissionDeniedError,
    PostNotFoundError,
)
from app.models import Group, Post, User
from app.repositories.group import GroupRepository
from app.repositories.post import PostRepository
from app.schemas import (
    CommentCreate,
    CommentRead,
    GroupDetail,
    LikeState,
    PostCreate,
    PostDetailResponse,
    PostList,
    PostUpdate,
)
from app.services.serializers import (
    comment_to_read,
    serialize_post_detail,
    serialize_post_page,
    serialize_posts,
)


class PostService:
    def __init__(self, post_repo: PostRepository, group_repo: GroupRepository):
        self.post_repo = post_repo
        self.group_repo = group_repo

    @property
    def session(self):
        return self.post_repo.session

    async def _check_group_access(self, group: Group | None, viewer: User | None) -> None:
        """Запрещает доступ к приватной группе не-участникам.

        Используется для действий, требующих членства (публикация, лайк,
        комментарий). Для чтения страницы группы применяется
        ``_can_view_group_posts``: метаданные видны всем, посты — нет.
        """
        if group is None or not group.is_private:
            return
        if viewer is None or not await self.group_repo.is_member(group.id, viewer.id):
            raise NotGroupMemberError("Группа приватная — вступите, чтобы видеть посты")

    async def _can_view_group_posts(self, group: Group, viewer: User | None) -> bool:
        if not group.is_private:
            return True
        if viewer is None:
            return False
        return await self.group_repo.is_member(group.id, viewer.id)

    async def _check_post_access(self, post: Post, viewer: User | None) -> None:
        if post.group_id is None:
            return
        group = await self.group_repo.get_by_id(post.group_id)
        await self._check_group_access(group, viewer)

    async def get_feed(
        self, q: str | None = None, params: Params | None = None, viewer: User | None = None
    ):
        viewer_id = viewer.id if viewer else None
        page = await self.post_repo.get_feed(q, params=params, viewer_id=viewer_id)
        return await serialize_post_page(self.session, page, viewer_id=viewer_id)

    async def get_follow_feed(self, current_user: User, params: Params | None = None):
        page = await self.post_repo.get_follow_feed(current_user.id, params=params)
        return await serialize_post_page(self.session, page, viewer_id=current_user.id)

    async def get_group_posts(
        self, slug: str, params: Params | None = None, viewer: User | None = None
    ):
        group = await self.group_repo.get_by_slug(slug)
        if not group:
            raise GroupNotFoundError("Сообщество не найдено")

        viewer_id = viewer.id if viewer else None
        is_member = viewer is not None and await self.group_repo.is_member(group.id, viewer.id)

        if await self._can_view_group_posts(group, viewer):
            page = await self.post_repo.get_group_posts(group.id, params=params)
            posts = await serialize_post_page(self.session, page, viewer_id=viewer_id)
        else:
            size = params.size if params else 10
            page_num = params.page if params else 1
            posts = Page(items=[], total=0, page=page_num, size=size, pages=0)

        group_detail = GroupDetail.model_validate(group)
        group_detail.members_count = await self.group_repo.count_members(group.id)
        group_detail.is_member = is_member

        return {"group": group_detail, "posts": posts}

    async def create_post(self, current_user: User, form: PostCreate) -> PostList:
        if form.group_id is not None:
            group = await self.group_repo.get_by_id(form.group_id)
            if not group:
                raise GroupNotFoundError("Сообщество не найдено")
            await self._check_group_access(group, current_user)

        images = form.images or ([form.image] if form.image else [])

        post = await self.post_repo.create(
            author_id=current_user.id,
            text=form.text,
            image=images[0] if images else None,
            group_id=form.group_id,
        )
        if images:
            await self.post_repo.set_images(post.id, images)

        fresh = await self.post_repo.get_by_id(post.id)
        return (await serialize_posts(self.session, [fresh], viewer_id=current_user.id))[0]

    async def edit_post(self, current_user: User, post_id: int, form: PostUpdate) -> PostList:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostNotFoundError("Пост не найден")
        if post.author_id != current_user.id:
            raise PermissionDeniedError("Только автор может редактировать пост")

        update_data = form.model_dump(exclude_unset=True)
        images = update_data.pop("images", None)

        if "group_id" in update_data and update_data["group_id"] is not None:
            group = await self.group_repo.get_by_id(update_data["group_id"])
            if not group:
                raise GroupNotFoundError("Сообщество не найдено")
            await self._check_group_access(group, current_user)

        if update_data:
            post = await self.post_repo.update(post, update_data)

        if images is not None:
            await self.post_repo.set_images(post.id, images)
            post.image = images[0] if images else None
            await self.session.flush()

        fresh = await self.post_repo.get_by_id(post.id)
        return (await serialize_posts(self.session, [fresh], viewer_id=current_user.id))[0]

    async def get_post_detail(self, post_id: int, viewer: User | None = None) -> PostDetailResponse:
        post = await self.post_repo.get_detail_by_id(post_id)
        if not post:
            raise PostNotFoundError("Пост не найден")

        await self._check_post_access(post, viewer)

        author_post_count = await self.post_repo.get_author_post_count(post.author_id)
        detail = await serialize_post_detail(
            self.session, post, viewer_id=viewer.id if viewer else None
        )
        return PostDetailResponse(post=detail, author_post_count=author_post_count)

    async def delete_post(self, current_user: User, post_id: int) -> None:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostNotFoundError("Пост не найден")
        if post.author_id != current_user.id:
            raise PermissionDeniedError("Вы можете удалить только свои посты")

        await self.post_repo.delete(post)

    # ---------- Лайки ----------

    async def like_post(self, current_user: User, post_id: int) -> LikeState:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostNotFoundError("Пост не найден")
        await self._check_post_access(post, current_user)

        await self.post_repo.add_like(post_id, current_user.id)
        count = await self.post_repo.count_likes(post_id)
        return LikeState(liked=True, likes_count=count)

    async def unlike_post(self, current_user: User, post_id: int) -> LikeState:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostNotFoundError("Пост не найден")
        await self._check_post_access(post, current_user)

        await self.post_repo.remove_like(post_id, current_user.id)
        count = await self.post_repo.count_likes(post_id)
        return LikeState(liked=False, likes_count=count)

    # ---------- Комментарии ----------

    async def add_comment(
        self, current_user: User, post_id: int, form: CommentCreate
    ) -> CommentRead:
        post = await self.post_repo.get_by_id(post_id)
        if not post:
            raise PostNotFoundError("Пост не найден")
        await self._check_post_access(post, current_user)

        parent_id = form.parent_id
        if parent_id is not None:
            parent = await self.post_repo.get_comment(parent_id)
            if not parent or parent.post_id != post_id:
                raise CommentNotFoundError("Родительский комментарий не найден")

        comment = await self.post_repo.add_comment(
            post_id=post_id,
            author_id=current_user.id,
            text=form.text,
            parent_id=parent_id,
        )
        return comment_to_read(comment)

    async def delete_comment(self, current_user: User, comment_id: int) -> None:
        comment = await self.post_repo.get_comment(comment_id)
        if not comment:
            raise CommentNotFoundError("Комментарий не найден")
        if comment.author_id != current_user.id:
            raise PermissionDeniedError("Можно удалять только свои комментарии")

        await self.post_repo.delete_comment(comment)
