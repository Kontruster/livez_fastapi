from pathlib import Path

UPLOAD_ROOT = Path("uploads")


def _try_delete_local_file(url: str | None) -> None:
    if not url or not url.startswith("/uploads/"):
        return
    rel = url.replace("/uploads/", "", 1)
    path = UPLOAD_ROOT / rel
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass