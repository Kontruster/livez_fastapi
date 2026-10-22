import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import UserManager, current_active_user, get_user_manager
from app.database import get_db
from app.dependencies import get_user_service
from app.models import User
from app.schemas import AccountDelete, PasswordChange, UsernameChange, UserRead
from app.services.user import UserService
from app.utils.files import save_image, try_delete_local_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/me", tags=["account"])

CurrentUser = Annotated[User, Depends(current_active_user)]
Session = Annotated[AsyncSession, Depends(get_db)]


# ---------- Смена username ----------
@router.patch("/profile", response_model=UserRead)
async def update_profile(
    form: UsernameChange,
    current_user: CurrentUser,
    session: Session,
    service: Annotated[UserService, Depends(get_user_service)],
):
    from app.exceptions import UsernameAlreadyExistsError

    new_username = form.username
    if new_username.lower() == current_user.username.lower():
        if new_username != current_user.username:
            current_user.username = new_username
            await session.flush()
            await session.refresh(current_user)
        return current_user

    if await service.user_repo.username_exists(new_username, exclude_id=current_user.id):
        raise UsernameAlreadyExistsError("Этот ник уже занят")

    current_user.username = new_username
    await session.flush()
    await session.refresh(current_user)
    return current_user


# ---------- Смена пароля ----------
@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    form: PasswordChange,
    current_user: CurrentUser,
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
):
    from fastapi import HTTPException

    verified, _ = user_manager.password_helper.verify_and_update(
        form.old_password, current_user.hashed_password
    )
    if not verified:
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")

    await user_manager.validate_password(form.new_password, current_user)

    new_hash = user_manager.password_helper.hash(form.new_password)
    # update() принимает словарь изменений, а не объект пользователя
    await user_manager.user_db.update(current_user, {"hashed_password": new_hash})
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- Загрузка аватара ----------
@router.post("/avatar", response_model=UserRead)
async def upload_avatar(
    current_user: CurrentUser,
    session: Session,
    file: Annotated[UploadFile, File()],
):
    old_url = current_user.avatar_url

    url, _path = await save_image(
        file,
        directory=settings.avatars_dir,
        max_bytes=settings.max_avatar_bytes,
        prefix=str(current_user.id),
    )

    current_user.avatar_url = url
    await session.flush()
    await session.refresh(current_user)

    # старый файл удаляем только после успешной записи нового URL
    if old_url and old_url != url:
        try_delete_local_file(old_url)

    return current_user


# ---------- Удаление аккаунта ----------
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    form: AccountDelete,
    current_user: CurrentUser,
    session: Session,
    user_manager: Annotated[UserManager, Depends(get_user_manager)],
):
    from fastapi import HTTPException
    from sqlalchemy import delete, or_, select

    from app.models import Comment, Follow, Post, PostImage

    verified, _ = user_manager.password_helper.verify_and_update(
        form.password, current_user.hashed_password
    )
    if not verified:
        raise HTTPException(status_code=400, detail="Неверный пароль")

    user_id = current_user.id
    post_ids = select(Post.id).where(Post.author_id == user_id)

    # собираем файлы ДО удаления записей, чтобы почистить диск
    image_urls = list(
        (await session.scalars(select(PostImage.url).where(PostImage.post_id.in_(post_ids)))).all()
    )
    image_urls += list(
        (await session.scalars(select(Post.image).where(Post.author_id == user_id))).all()
    )
    avatar_url = current_user.avatar_url

    await session.execute(delete(Comment).where(Comment.author_id == user_id))
    await session.execute(delete(Comment).where(Comment.post_id.in_(post_ids)))
    await session.execute(delete(Post).where(Post.author_id == user_id))
    await session.execute(
        delete(Follow).where(or_(Follow.user_id == user_id, Follow.author_id == user_id))
    )
    await session.execute(delete(User).where(User.id == user_id))
    await session.flush()

    for url in [*image_urls, avatar_url]:
        try_delete_local_file(url)

    resp = Response(status_code=status.HTTP_204_NO_CONTENT)
    resp.delete_cookie("fastapiusersauth")
    return resp
