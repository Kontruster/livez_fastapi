from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

# Репозитории
from app.repositories.post import PostRepository
from app.repositories.user import UserRepository
from app.repositories.group import GroupRepository

# Сервисы
from app.services.post import PostService
from app.services.user import UserService
from app.services.group import GroupService

def get_post_repo(session: AsyncSession = Depends(get_db)) -> PostRepository:
    return PostRepository(session)

def get_user_repo(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)

def get_group_repo(session: AsyncSession = Depends(get_db)) -> GroupRepository:
    return GroupRepository(session)

def get_post_service(
    post_repo: PostRepository = Depends(get_post_repo),
    group_repo: GroupRepository = Depends(get_group_repo)
) -> PostService:
    return PostService(post_repo, group_repo)

def get_user_service(user_repo: UserRepository = Depends(get_user_repo)) -> UserService:
    return UserService(user_repo)

def get_group_service(group_repo: GroupRepository = Depends(get_group_repo)) -> GroupService:
    return GroupService(group_repo)
