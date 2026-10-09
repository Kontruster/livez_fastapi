from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.auth import current_active_user, current_optional_user
from app.dependencies import get_group_service, get_post_service, get_user_service
from app.models import User
from app.schemas import (
    CommentCreate,
    CommentRead,
    GroupCreate,
    GroupDetail,
    GroupDetailResponse,
    GroupRead,
    LikeState,
    PostCreate,
    PostDetailResponse,
    PostList,
    PostUpdate,
    ProfileResponse,
)
from app.services.group import GroupService
from app.services.post import PostService
from app.services.user import UserService

router = APIRouter(tags=["posts"])

CurrentUser = Annotated[User, Depends(current_active_user)]
OptionalUser = Annotated[User | None, Depends(current_optional_user)]


def _pagination(
    page: Annotated[int, Query(ge=1, description="Номер страницы")] = 1,
    size: Annotated[int, Query(ge=1, le=100, description="Размер страницы")] = 10,
) -> Params:
    """Параметры пагинации: по умолчанию 10 записей на страницу, максимум 100."""
    return Params(page=page, size=size)


PaginationParams = Annotated[Params, Depends(_pagination)]


# ---------- Лента ----------


@router.get("/posts/", response_model=Page[PostList])
async def index(
    service: Annotated[PostService, Depends(get_post_service)],
    params: PaginationParams,
    q: Annotated[str | None, Query(description="Поиск по тексту")] = None,
    current_user: OptionalUser = None,
):
    return await service.get_feed(q, params, current_user)


@router.get("/follow/", response_model=Page[PostList])
async def follow_index(
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
    params: PaginationParams,
):
    return await service.get_follow_feed(current_user, params)


@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def post_detail(
    post_id: int,
    service: Annotated[PostService, Depends(get_post_service)],
    current_user: OptionalUser = None,
):
    return await service.get_post_detail(post_id, current_user)


# ---------- CRUD постов ----------


@router.post("/posts/", response_model=PostList, status_code=status.HTTP_201_CREATED)
async def create_post(
    form: PostCreate,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.create_post(current_user, form)


@router.patch("/posts/{post_id}/", response_model=PostList)
async def edit_post(
    post_id: int,
    form: PostUpdate,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.edit_post(current_user, post_id, form)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    await service.delete_post(current_user, post_id)


# ---------- Лайки ----------


@router.post("/posts/{post_id}/like/", response_model=LikeState)
async def like_post(
    post_id: int,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.like_post(current_user, post_id)


@router.delete("/posts/{post_id}/like/", response_model=LikeState)
async def unlike_post(
    post_id: int,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.unlike_post(current_user, post_id)


# ---------- Комментарии ----------


@router.post(
    "/posts/{post_id}/comments/",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_comment(
    post_id: int,
    form: CommentCreate,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    return await service.add_comment(current_user, post_id, form)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: CurrentUser,
    service: Annotated[PostService, Depends(get_post_service)],
):
    await service.delete_comment(current_user, comment_id)


# ---------- Профили ----------


@router.get("/profile/me", response_model=ProfileResponse)
async def my_profile(
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
    params: PaginationParams,
):
    return await service.get_profile(current_user.username, current_user, params)


@router.get("/profile/{username}", response_model=ProfileResponse)
async def user_profile(
    username: str,
    service: Annotated[UserService, Depends(get_user_service)],
    params: PaginationParams,
    current_user: OptionalUser = None,
):
    return await service.get_profile(username, current_user, params)


@router.post("/profile/{username}/follow/", status_code=status.HTTP_201_CREATED)
async def follow_user(
    username: str,
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    return await service.follow_user(current_user, username)


@router.delete("/profile/{username}/follow/", status_code=status.HTTP_200_OK)
async def unfollow_user(
    username: str,
    current_user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
):
    return await service.unfollow_user(current_user, username)


# ---------- Группы ----------


@router.get("/groups/", response_model=list[GroupRead])
async def list_groups(
    service: Annotated[GroupService, Depends(get_group_service)],
):
    return await service.get_all_groups()


@router.get("/groups/{slug}/", response_model=GroupDetailResponse)
async def group_posts(
    slug: str,
    service: Annotated[PostService, Depends(get_post_service)],
    params: PaginationParams,
    current_user: OptionalUser = None,
):
    return await service.get_group_posts(slug, params, current_user)


@router.post("/groups/", response_model=GroupRead, status_code=status.HTTP_201_CREATED)
async def create_group(
    form: GroupCreate,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    return await service.create_group(form, current_user)


@router.post("/groups/{slug}/join/", response_model=GroupDetail)
async def join_group(
    slug: str,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    return await service.join_group(slug, current_user)


@router.delete("/groups/{slug}/leave/", response_model=GroupDetail)
async def leave_group(
    slug: str,
    current_user: CurrentUser,
    service: Annotated[GroupService, Depends(get_group_service)],
):
    return await service.leave_group(slug, current_user)
