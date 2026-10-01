import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import current_active_user, get_user_manager, UserManager
from app.database import get_db
from app.models import User, Post, Comment, Follow
from app.schemas import UserRead, UsernameChange, PasswordChange, AccountDelete

router = APIRouter(prefix="/users/me", tags=["account"])

UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": "jpg",
    "image/png":  "png",
    "image/webp": "webp",
    "image/gif":  "gif",
}
MAX_AVATAR_BYTES = 5 * 1024 * 1024  # 5 МБ


# ---------- Смена username ----------
@router.patch("/profile", response_model=UserRead)
async def update_profile(
    form: UsernameChange,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
):
    new_username = form.username.strip()
    if new_username == current_user.username:
        return current_user

    existing = await session.scalar(
        select(User).where(User.username == new_username)
    )
    if existing:
        raise HTTPException(409, "Этот ник уже занят")

    current_user.username = new_username
    await session.commit()
    await session.refresh(current_user)
    return current_user


# ---------- Смена пароля ----------
@router.post("/password", status_code=204)
async def change_password(
    form: PasswordChange,
    user_manager: UserManager = Depends(get_user_manager),
    current_user: User = Depends(current_active_user),
):
    verified, _ = user_manager.password_helper.verify_and_update(
        form.old_password, current_user.hashed_password
    )
    if not verified:
        raise HTTPException(400, "Неверный текущий пароль")

    # validate новый пароль через fastapi-users
    await user_manager.validate_password(form.new_password, current_user)

    new_hash = user_manager.password_helper.hash(form.new_password)
    current_user.hashed_password = new_hash
    await user_manager.user_db.update(current_user)
    return Response(status_code=204)


# ---------- Загрузка аватара ----------
@router.post("/avatar", response_model=UserRead)
async def upload_avatar(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(current_active_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Только изображения: JPEG, PNG, WEBP, GIF")

    content = await file.read()
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(413, "Файл больше 5 МБ")

    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    path = UPLOAD_DIR / filename
    path.write_bytes(content)

    if current_user.avatar_url:
        old = Path("uploads") / current_user.avatar_url.replace("/uploads/", "")
        old.unlink(missing_ok=True)

    current_user.avatar_url = f"/uploads/avatars/{filename}"
    await session.commit()
    await session.refresh(current_user)
    return current_user


# ---------- Удаление аккаунта ----------
@router.delete("", status_code=204)
async def delete_me(
    form: AccountDelete,
    session: AsyncSession = Depends(get_db),
    user_manager: UserManager = Depends(get_user_manager),
    current_user: User = Depends(current_active_user),
):
    verified, _ = user_manager.password_helper.verify_and_update(
        form.password, current_user.hashed_password
    )
    if not verified:
        raise HTTPException(400, "Неверный пароль")

    user_post_ids = select(Post.id).where(Post.author_id == current_user.id)

    await session.execute(delete(Comment).where(Comment.author_id == current_user.id))
    await session.execute(delete(Comment).where(Comment.post_id.in_(user_post_ids)))
    await session.execute(delete(Post).where(Post.author_id == current_user.id))
    await session.execute(
        delete(Follow).where(
            or_(Follow.user_id == current_user.id, Follow.author_id == current_user.id)
        )
    )
    await session.execute(delete(User).where(User.id == current_user.id))
    await session.commit()

    resp = Response(status_code=204)
    resp.delete_cookie("fastapiusersauth")
    return resp