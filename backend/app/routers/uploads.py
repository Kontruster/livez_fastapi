from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import settings
from app.core.auth import current_active_user
from app.models import User
from app.schemas import PostImageRead
from app.utils.files import save_image

router = APIRouter(prefix="/media", tags=["uploads"])


@router.post("/post-image", response_model=PostImageRead)
async def upload_post_image(
    current_user: Annotated[User, Depends(current_active_user)],
    file: Annotated[UploadFile, File()],
):
    url, _path = await save_image(
        file,
        directory=settings.post_images_dir,
        max_bytes=settings.max_upload_bytes,
        prefix=str(current_user.id),
    )
    return {"id": 0, "url": url, "position": 0}
