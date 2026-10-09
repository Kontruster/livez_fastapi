"""Тесты аутентификации и аккаунта."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_register_login_logout(client, user_factory):
    creds = user_factory("reg")

    resp = await client.post("/auth/register", json=creds)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == creds["email"]
    assert body["username"] == creds["username"]
    assert "hashed_password" not in body

    resp = await client.post(
        "/auth/jwt/login",
        data={"username": creds["email"], "password": creds["password"]},
    )
    # fastapi-users отдаёт 204 на успешный логин (токен в cookie)
    assert resp.status_code == 204

    resp = await client.get("/users/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == creds["username"]

    resp = await client.post("/auth/jwt/logout")
    assert resp.status_code in (200, 204)

    resp = await client.get("/users/me")
    assert resp.status_code == 401


async def test_duplicate_email_rejected(client, user_factory):
    creds = user_factory("dup")
    assert (await client.post("/auth/register", json=creds)).status_code == 201

    again = user_factory("dup2")
    again["email"] = creds["email"]
    resp = await client.post("/auth/register", json=again)
    assert resp.status_code == 400


async def test_short_password_rejected(client, user_factory):
    creds = user_factory("short")
    creds["password"] = "123"
    resp = await client.post("/auth/register", json=creds)
    # UserManager.validate_password бросает HTTPException(400)
    assert resp.status_code in (400, 422)


async def test_invalid_username_rejected(client, user_factory):
    creds = user_factory("badname")
    creds["username"] = "плохое имя!"
    resp = await client.post("/auth/register", json=creds)
    assert resp.status_code == 422


async def test_me_requires_auth(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401


async def test_change_username(auth_client):
    client, _me = auth_client
    resp = await client.patch("/users/me/profile", json={"username": "newnick123"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["username"] == "newnick123"


async def test_change_username_conflict(auth_client, second_client):
    client, _me = auth_client
    other = (await second_client.get("/users/me")).json()

    resp = await client.patch("/users/me/profile", json={"username": other["username"]})
    assert resp.status_code == 409


async def test_change_password(auth_client, user_factory):
    client, me = auth_client

    resp = await client.post(
        "/users/me/password",
        json={"old_password": "supersecret123", "new_password": "brandnewpass456"},
    )
    assert resp.status_code == 204, resp.text

    # старый пароль больше не работает
    resp = await client.post(
        "/auth/jwt/login",
        data={"username": me["email"], "password": "supersecret123"},
    )
    assert resp.status_code == 400

    resp = await client.post(
        "/auth/jwt/login",
        data={"username": me["email"], "password": "brandnewpass456"},
    )
    assert resp.status_code == 204


async def test_change_password_wrong_old(auth_client):
    client, _me = auth_client
    resp = await client.post(
        "/users/me/password",
        json={"old_password": "wrong-password", "new_password": "brandnewpass456"},
    )
    assert resp.status_code == 400


async def test_delete_account(auth_client, second_client):
    """Удаление аккаунта уносит его посты и комментарии, не ломая чужие."""
    client, _me = auth_client

    post = (await client.post("/posts/", json={"text": "пост на удаление"})).json()
    other_post = (await second_client.post("/posts/", json={"text": "чужой пост"})).json()
    await second_client.post(f"/posts/{post['id']}/comments/", json={"text": "чужой комментарий"})

    resp = await client.request("DELETE", "/users/me", json={"password": "supersecret123"})
    assert resp.status_code == 204, resp.text

    # пользователя больше нет
    resp = await client.get("/users/me")
    assert resp.status_code == 401

    # его пост исчез вместе с комментариями к нему
    resp = await second_client.get(f"/posts/{post['id']}")
    assert resp.status_code == 404

    # чужой пост цел, комментарий к нему удалён каскадом
    resp = await second_client.get(f"/posts/{other_post['id']}")
    assert resp.status_code == 200
    assert resp.json()["post"]["comments"] == []


async def test_delete_account_wrong_password(auth_client):
    client, _me = auth_client
    resp = await client.request("DELETE", "/users/me", json={"password": "nope"})
    assert resp.status_code == 400
