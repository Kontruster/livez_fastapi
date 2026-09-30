import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page

from app.core.auth import current_active_user
from app.database import get_db
from app.dependencies import (get_group_service, get_post_service,
                              get_user_service)
from app.exceptions import (CannotFollowSelfError, GroupNotFoundError,
                            PermissionDeniedError, PostNotFoundError,
                            UserNotFoundError)
from app.models import User
from app.schemas import *
from app.services.group import GroupService
from app.services.post import PostService
from app.services.user import UserService

router = APIRouter(tags=["posts"])


logger = logging.getLogger(__name__)

def handle_domain_exception(exc: Exception):
    if isinstance(exc, PostNotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionDeniedError):
        raise HTTPException(status_code=403, detail=str(exc))
    logger.exception("Unhandled error in router: %s", exc)
    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

@router.get("/posts/", response_model=Page[PostList])
async def index(
    q: Optional[str] = Query(None, description="Поиск по тексту"),
    service: PostService = Depends(get_post_service),
):
   try:
       return await service.get_feed(q)
   except Exception as e:
       handle_domain_exception(e)


@router.get("/follow/", response_model=Page[PostList])
async def follow_index(
    service: PostService = Depends(get_post_service),
    current_user: User = Depends(current_active_user),
):
    try:
        return await service.get_follow_feed(current_user)
    except Exception as e:
        handle_domain_exception(e)


@router.get("/groups/{slug}/", response_model=Page[PostList])
async def group_posts(
    slug: str,
    service: PostService = Depends(get_post_service),
):
    try:
        return await service.get_group_posts(slug)
    except Exception as e:
        handle_domain_exception(e)


@router.post("/posts/", response_model=PostList, status_code=status.HTTP_201_CREATED)
async def create_post(
    form: PostCreate,
    service: PostService = Depends(get_post_service),
    current_user: User = Depends(current_active_user)
):
    try:
        return await service.create_post(current_user, form)
    except Exception as e:
        handle_domain_exception(e)

@router.patch("/posts/{post_id}/", response_model=PostList)
async def edit_post(
    post_id: int,
    form: PostCreate,
    current_user: User = Depends(current_active_user),
    service: PostService = Depends(get_post_service),
):
    try:
        return await service.edit_post(current_user, post_id, form)
    except Exception as e:
        handle_domain_exception(e)

@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(
    post_id: int,
    service: PostService = Depends(get_post_service),
    current_user: User = Depends(current_active_user),
):
    try:
        await service.delete_post(current_user, post_id)
        return {"status": "ok"}
    except PostNotFoundError:
        raise HTTPException(status_code=404, detail="Не найдено")
    except PermissionDeniedError:
        raise HTTPException(status_code=403, detail="Запрещено")

@router.get("/profile/me", response_model=ProfileResponse)
async def my_profile(
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
):
    try:
        return await service.get_profile(current_user.username, current_user)
    except Exception as e:
        handle_domain_exception(e)

@router.get("/profile/{username}", response_model=ProfileResponse)
async def user_profile(
    username: str,
    service: UserService = Depends(get_user_service),
    current_user: Optional[User] = Depends(current_active_user),
):
    try:
        return await service.get_profile(username, current_user)
    except Exception as e:
        handle_domain_exception(e)


@router.get("/posts/{post_id}", response_model=PostDetailResponse)
async def post_detail(
    post_id: int,
    service: PostService = Depends(get_post_service),
):
    try:
        return await service.get_post_detail(post_id)
    except PostNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        handle_domain_exception(e)


@router.get("/groups/", response_model=list[GroupRead])
async def list_groups(
    service: GroupService = Depends(get_group_service),
):
    try:
        return await service.get_all_groups()
    except Exception as e:
        handle_domain_exception(e)


@router.post("/posts/{post_id}/comments/", response_model=CommentRead, status_code=201)
async def add_comment(
    post_id: int,
    form: CommentCreate,
    service: PostService = Depends(get_post_service),
    current_user: User = Depends(current_active_user),
):
    try:
        return await service.add_comment(current_user, post_id, form)
    except PostNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        handle_domain_exception(e)


@router.post("/profile/{username}/follow/", status_code=201)
async def follow_user(
    username: str,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
):
    try:
        return await service.follow_user(current_user, username)
    except CannotFollowSelfError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PostNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        handle_domain_exception(e)

@router.delete("/profile/{username}/follow/")
async def unfollow_user(
    username: str,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(current_active_user),
):
    try:
        await service.unfollow_user(current_user, username)
        return {"status": "unfollowed"}
    except PostNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        handle_domain_exception(e)