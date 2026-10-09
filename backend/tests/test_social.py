"""Тесты комментариев, подписок, групп и загрузки файлов."""

import struct
import zlib

import pytest

pytestmark = pytest.mark.asyncio


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def make_png(size: tuple[int, int] = (8, 8)) -> bytes:
    """Собирает валидный PNG вручную, без внешних библиотек."""
    width, height = size
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x78\x1e\xc8" * width for _ in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )


def make_jpeg() -> bytes:
    """Минимальный валидный JPEG (сигнатура + маркеры + EOI)."""
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00\x43\x00"
        + b"\x08" * 64
        + b"\xff\xc0\x00\x0b\x08\x00\x08\x00\x08\x01\x01\x11\x00"
        + b"\xff\xc4\x00\x1f\x00"
        + b"\x00" * 31
        + b"\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00"
        + b"\xff\xd9"
    )


def make_gif() -> bytes:
    return b"GIF89a" + b"\x01\x00\x01\x00" + b"\x00" * 20 + b"\x3b"


# ---------- Комментарии ----------


async def test_add_comment_increments_count(auth_client):
    client, me = auth_client
    post = (await client.post("/posts/", json={"text": "комментируемый"})).json()

    resp = await client.post(f"/posts/{post['id']}/comments/", json={"text": "первый!"})
    assert resp.status_code == 201, resp.text
    comment = resp.json()
    assert comment["text"] == "первый!"
    assert comment["author"]["username"] == me["username"]

    resp = await client.get(f"/posts/{post['id']}")
    assert resp.json()["post"]["comments_count"] == 1
    assert len(resp.json()["post"]["comments"]) == 1

    resp = await client.get("/posts/")
    item = next(p for p in resp.json()["items"] if p["id"] == post["id"])
    assert item["comments_count"] == 1


async def test_comment_on_missing_post(auth_client):
    client, _me = auth_client
    resp = await client.post("/posts/999999/comments/", json={"text": "нет поста"})
    assert resp.status_code == 404


async def test_comment_requires_auth(session_maker, user_factory):
    """Без cookie комментарий создать нельзя, даже если пост существует."""
    from httpx import ASGITransport, AsyncClient

    from app.database import get_db
    from app.main import app

    async def override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    # автор создаёт пост
    async with AsyncClient(transport=transport, base_url="http://test") as author:
        creds = user_factory("author")
        await author.post("/auth/register", json=creds)
        await author.post(
            "/auth/jwt/login",
            data={"username": creds["email"], "password": creds["password"]},
        )
        post = (await author.post("/posts/", json={"text": "пост"})).json()

    # анонимный клиент без cookie
    async with AsyncClient(transport=transport, base_url="http://test") as anon:
        resp = await anon.post(f"/posts/{post['id']}/comments/", json={"text": "аноним"})
        assert resp.status_code == 401


async def test_comment_empty_rejected(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()
    resp = await client.post(f"/posts/{post['id']}/comments/", json={"text": "  "})
    assert resp.status_code == 422


async def test_delete_own_comment(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()
    comment = (await client.post(f"/posts/{post['id']}/comments/", json={"text": "мой"})).json()

    resp = await client.delete(f"/comments/{comment['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"/posts/{post['id']}")
    assert resp.json()["post"]["comments_count"] == 0


async def test_delete_foreign_comment_forbidden(auth_client, second_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()
    comment = (await client.post(f"/posts/{post['id']}/comments/", json={"text": "мой"})).json()

    resp = await second_client.delete(f"/comments/{comment['id']}")
    assert resp.status_code == 403


# ---------- Подписки ----------


async def test_follow_and_unfollow(auth_client, second_client):
    client, _me = auth_client
    other = (await second_client.get("/users/me")).json()

    resp = await client.post(f"/profile/{other['username']}/follow/")
    assert resp.status_code == 201, resp.text

    resp = await client.get(f"/profile/{other['username']}")
    assert resp.json()["is_following"] is True
    assert resp.json()["followers_count"] == 1

    # повторная подписка не ломается и не дублируется
    resp = await client.post(f"/profile/{other['username']}/follow/")
    assert resp.status_code == 201
    resp = await client.get(f"/profile/{other['username']}")
    assert resp.json()["followers_count"] == 1

    resp = await client.delete(f"/profile/{other['username']}/follow/")
    assert resp.status_code == 200
    resp = await client.get(f"/profile/{other['username']}")
    assert resp.json()["is_following"] is False
    assert resp.json()["followers_count"] == 0


async def test_cannot_follow_self(auth_client):
    client, me = auth_client
    resp = await client.post(f"/profile/{me['username']}/follow/")
    assert resp.status_code == 422


async def test_follow_missing_user(auth_client):
    client, _me = auth_client
    resp = await client.post("/profile/nobody_here_xyz/follow/")
    assert resp.status_code == 404


async def test_follow_feed(auth_client, second_client):
    client, _me = auth_client
    other = (await second_client.get("/users/me")).json()

    # без подписок лента пуста
    resp = await client.get("/follow/")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0

    await second_client.post("/posts/", json={"text": "пост того, на кого подписан"})
    await client.post("/posts/", json={"text": "мой собственный пост"})

    await client.post(f"/profile/{other['username']}/follow/")

    resp = await client.get("/follow/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["author"]["username"] == other["username"]


async def test_follow_feed_requires_auth(client):
    resp = await client.get("/follow/")
    assert resp.status_code == 401


# ---------- Группы ----------


async def test_create_and_list_groups(auth_client):
    client, _me = auth_client
    resp = await client.post(
        "/groups/",
        json={"title": "Коты", "slug": "koty", "description": "про котов"},
    )
    assert resp.status_code == 201, resp.text

    resp = await client.get("/groups/")
    assert resp.status_code == 200
    assert any(g["slug"] == "koty" for g in resp.json())


async def test_duplicate_group_slug_conflict(auth_client):
    client, _me = auth_client
    payload = {"title": "Дубль", "slug": "dubl", "description": ""}
    assert (await client.post("/groups/", json=payload)).status_code == 201
    assert (await client.post("/groups/", json=payload)).status_code == 409


async def test_invalid_group_slug(auth_client):
    client, _me = auth_client
    resp = await client.post(
        "/groups/", json={"title": "Плохой", "slug": "ПЛОХОЙ slug", "description": ""}
    )
    assert resp.status_code == 422


async def test_group_feed(auth_client):
    client, _me = auth_client
    group = (
        await client.post("/groups/", json={"title": "Группа", "slug": "gruppa", "description": ""})
    ).json()
    await client.post("/posts/", json={"text": "в группе", "group_id": group["id"]})
    await client.post("/posts/", json={"text": "вне группы"})

    resp = await client.get(f"/groups/{group['slug']}/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["group"]["slug"] == "gruppa"
    assert body["posts"]["total"] == 1
    assert body["posts"]["items"][0]["text"] == "в группе"


async def test_group_feed_missing(client):
    resp = await client.get("/groups/net-takoy-gruppy/")
    assert resp.status_code == 404


# ---------- Загрузка файлов ----------


async def test_upload_post_image(auth_client):
    client, me = auth_client
    resp = await client.post(
        "/media/post-image",
        files={"file": ("pic.png", make_png(), "image/png")},
    )
    assert resp.status_code == 200, resp.text
    url = resp.json()["url"]
    assert url.startswith("/uploads/posts/")
    assert url.endswith(".png")
    assert str(me["id"]) in url


async def test_upload_rejects_non_image(auth_client):
    """Подделанный content-type не проходит: проверяются магические байты."""
    client, _me = auth_client
    resp = await client.post(
        "/media/post-image",
        files={"file": ("evil.png", b"<html><script>alert(1)</script>", "image/png")},
    )
    assert resp.status_code == 415


async def test_upload_requires_auth(client):
    resp = await client.post(
        "/media/post-image",
        files={"file": ("pic.png", make_png(), "image/png")},
    )
    assert resp.status_code == 401


async def test_avatar_upload_and_replace(auth_client):
    """Повторная загрузка аватара не падает и удаляет старый файл."""
    client, _me = auth_client

    resp = await client.post("/users/me/avatar", files={"file": ("a.png", make_png(), "image/png")})
    assert resp.status_code == 200, resp.text
    first = resp.json()["avatar_url"]
    assert first.startswith("/uploads/avatars/")

    resp = await client.post(
        "/users/me/avatar", files={"file": ("b.jpg", make_jpeg(), "image/jpeg")}
    )
    assert resp.status_code == 200, resp.text
    second = resp.json()["avatar_url"]

    assert second != first
    assert second.endswith(".jpg")

    # старый файл действительно удалён с диска
    from app.config import settings

    old_name = first.rsplit("/", 1)[-1]
    assert not (settings.avatars_dir / old_name).exists()


async def test_avatar_rejects_fake_image(auth_client):
    client, _me = auth_client
    resp = await client.post(
        "/users/me/avatar",
        files={"file": ("fake.jpg", b"not an image at all", "image/jpeg")},
    )
    assert resp.status_code == 415


async def test_avatar_rejects_oversized(auth_client):
    """Файл больше лимита аватара отклоняется по 413."""
    client, _me = auth_client
    big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (6 * 1024 * 1024)
    resp = await client.post("/users/me/avatar", files={"file": ("big.png", big, "image/png")})
    assert resp.status_code == 413


# ---------- Сервис ----------


async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
