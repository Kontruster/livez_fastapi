"""Работа с локальными файлами загрузок."""

import logging
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.exceptions import PayloadTooLargeError, UnsupportedMediaTypeError

logger = logging.getLogger(__name__)

UPLOAD_ROOT = settings.UPLOAD_DIR

# Разрешённые форматы: content-type -> (расширение, список «магических» сигнатур)
IMAGE_SIGNATURES: dict[str, tuple[str, tuple[bytes, ...]]] = {
    "image/jpeg": ("jpg", (b"\xff\xd8\xff",)),
    "image/png": ("png", (b"\x89PNG\r\n\x1a\n",)),
    "image/webp": ("webp", (b"RIFF",)),
    "image/gif": ("gif", (b"GIF87a", b"GIF89a")),
}

ALLOWED_TYPES = {k: v[0] for k, v in IMAGE_SIGNATURES.items()}


def _url_to_path(url: str | None) -> Path | None:
    """Преобразует публичный URL ``/uploads/...`` в путь на диске."""
    if not url or not url.startswith("/uploads/"):
        return None
    rel = url.removeprefix("/uploads/")
    candidate = (UPLOAD_ROOT / rel).resolve()
    root = UPLOAD_ROOT.resolve()
    # защита от «../» в URL: файл обязан лежать внутри uploads/
    if root != candidate and root not in candidate.parents:
        logger.warning("Попытка выйти за пределы uploads/: %s", url)
        return None
    return candidate


def try_delete_local_file(url: str | None) -> Path | None:
    """Удаляет локальный файл по публичному URL.

    Возвращает путь, если файл существовал и был удалён, иначе ``None``.
    Никогда не бросает исключений — уборка мусора не должна ломать запрос.
    """
    path = _url_to_path(url)
    if path is None:
        return None
    try:
        if not path.is_file():
            return None
        path.unlink()
        return path
    except OSError as exc:
        logger.warning("Не удалось удалить файл %s: %s", path, exc)
        return None


# обратная совместимость со старым приватным именем
_try_delete_local_file = try_delete_local_file


def _detect_image_type(header: bytes) -> str | None:
    """Определяет тип картинки по «магическим» байтам."""
    for content_type, (_, signatures) in IMAGE_SIGNATURES.items():
        for sig in signatures:
            if header.startswith(sig):
                if content_type == "image/webp" and header[8:12] != b"WEBP":
                    continue
                return content_type
    return None


async def save_image(
    file: UploadFile,
    directory: Path,
    max_bytes: int,
    prefix: str,
) -> tuple[str, Path]:
    """Проверяет и сохраняет загруженную картинку.

    Проверка идёт по содержимому файла, а не по заголовку Content-Type,
    который клиент может подделать. Возвращает ``(публичный_url, путь)``.
    """
    content = await file.read()

    if len(content) > max_bytes:
        raise PayloadTooLargeError(f"Файл больше {max_bytes // (1024 * 1024)} МБ")
    if not content:
        raise UnsupportedMediaTypeError("Пустой файл")

    detected = _detect_image_type(content[:16])
    if detected is None:
        raise UnsupportedMediaTypeError("Только изображения: JPEG, PNG, WEBP, GIF")

    declared = (file.content_type or "").lower()
    if declared and declared not in IMAGE_SIGNATURES:
        raise UnsupportedMediaTypeError("Только изображения: JPEG, PNG, WEBP, GIF")
    if declared and declared != detected:
        logger.info(
            "Content-Type %s не совпал с содержимым %s — доверяем содержимому",
            declared,
            detected,
        )

    ext = IMAGE_SIGNATURES[detected][0]
    filename = f"{prefix}_{uuid.uuid4().hex[:10]}.{ext}"

    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_bytes(content)

    return f"/uploads/{directory.name}/{filename}", path
