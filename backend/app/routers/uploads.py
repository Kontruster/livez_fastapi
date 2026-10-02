import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.core.auth import current_active_user
from app.models import User

router = APIRouter(prefix="/media", tags=["uploads"])

POST_UPLOAD_DIR = Path("uploads/posts")
POST_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {
    "image/jpeg": "jpg",
    "image/png":  "png",
    "image/webp": "webp",
    "image/gif":  "gif",
}
MAX_BYTES = 10 * 1024 * 1024  # 10 МБ


@router.post("/post-image")
async def upload_post_image(
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, "Только изображения: JPEG, PNG, WEBP, GIF")

    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Файл больше 10 МБ")

    ext = ALLOWED_TYPES[file.content_type]
    filename = f"{current_user.id}_{uuid.uuid4().hex[:10]}.{ext}"
    path = POST_UPLOAD_DIR / filename
    path.write_bytes(content)

    return {"url": f"/uploads/posts/{filename}"}