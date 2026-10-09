from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.group import GroupRepository

# Репозитории
from app.repositories.post import PostRepository
from app.repositories.user import UserRepository
from app.services.group import GroupService

# Сервисы
from app.services.post import PostService
from app.services.user import UserService

SessionDep = Annotated[AsyncSession, Depends(get_db)]


def get_post_repo(session: SessionDep) -> PostRepository:
    return PostRepository(session)


def get_user_repo(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_group_repo(session: SessionDep) -> GroupRepository:
    return GroupRepository(session)


def get_post_service(
    post_repo: Annotated[PostRepository, Depends(get_post_repo)],
    group_repo: Annotated[GroupRepository, Depends(get_group_repo)],
) -> PostService:
    return PostService(post_repo, group_repo)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> UserService:
    return UserService(user_repo)


def get_group_service(
    group_repo: Annotated[GroupRepository, Depends(get_group_repo)],
) -> GroupService:
    return GroupService(group_repo)
