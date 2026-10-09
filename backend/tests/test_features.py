"""Тесты лайков, ответов на комментарии, приватных групп и счётчиков подписок."""

import pytest

pytestmark = pytest.mark.asyncio


# ---------- Лайки ----------


async def test_like_and_unlike(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "лайкни меня"})).json()
    assert post["likes_count"] == 0
    assert post["is_liked"] is False

    resp = await client.post(f"/posts/{post['id']}/like/")
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"liked": True, "likes_count": 1}

    # лайк видно в детали поста
    detail = (await client.get(f"/posts/{post['id']}")).json()["post"]
    assert detail["likes_count"] == 1
    assert detail["is_liked"] is True

    resp = await client.delete(f"/posts/{post['id']}/like/")
    assert resp.status_code == 200
    assert resp.json() == {"liked": False, "likes_count": 0}

    detail = (await client.get(f"/posts/{post['id']}")).json()["post"]
    assert detail["likes_count"] == 0
    assert detail["is_liked"] is False


async def test_like_is_idempotent(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()

    await client.post(f"/posts/{post['id']}/like/")
    resp = await client.post(f"/posts/{post['id']}/like/")
    assert resp.json()["likes_count"] == 1

    # повторный анлайк тоже безопасен
    await client.delete(f"/posts/{post['id']}/like/")
    resp = await client.delete(f"/posts/{post['id']}/like/")
    assert resp.json()["likes_count"] == 0


async def test_likes_from_two_users(auth_client, second_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "общий пост"})).json()

    await client.post(f"/posts/{post['id']}/like/")
    resp = await second_client.post(f"/posts/{post['id']}/like/")
    assert resp.json()["likes_count"] == 2

    # у второго пользователя is_liked = True, у него свой статус
    detail = (await second_client.get(f"/posts/{post['id']}")).json()["post"]
    assert detail["likes_count"] == 2
    assert detail["is_liked"] is True

    await second_client.delete(f"/posts/{post['id']}/like/")
    detail_via_first = (await client.get(f"/posts/{post['id']}")).json()["post"]
    assert detail_via_first["likes_count"] == 1
    assert detail_via_first["is_liked"] is True


async def test_feed_exposes_likes(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "в ленте"})).json()
    await client.post(f"/posts/{post['id']}/like/")

    resp = await client.get("/posts/")
    item = next(p for p in resp.json()["items"] if p["id"] == post["id"])
    assert item["likes_count"] == 1
    assert item["is_liked"] is True


async def test_anonymous_feed_has_no_liked_state(anon_client, auth_client):
    authed, _me = auth_client
    post = (await authed.post("/posts/", json={"text": "публичный"})).json()
    await authed.post(f"/posts/{post['id']}/like/")

    # аноним видит счётчик, но is_liked всегда False
    resp = await anon_client.get("/posts/")
    item = next(p for p in resp.json()["items"] if p["id"] == post["id"])
    assert item["likes_count"] == 1
    assert item["is_liked"] is False


async def test_like_requires_auth(anon_client):
    resp = await anon_client.post("/posts/1/like/")
    assert resp.status_code == 401


async def test_like_missing_post(auth_client):
    client, _me = auth_client
    resp = await client.post("/posts/999999/like/")
    assert resp.status_code == 404


async def test_likes_removed_with_post(auth_client, db_session):
    """Удаление поста уносит его лайки (иначе остаются сироты)."""
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "удаляемый"})).json()
    await client.post(f"/posts/{post['id']}/like/")

    assert (await client.delete(f"/posts/{post['id']}")).status_code == 204

    from sqlalchemy import func, select

    from app.models import PostLike

    count = await db_session.scalar(
        select(func.count(PostLike.id)).where(PostLike.post_id == post["id"])
    )
    assert count == 0


# ---------- Комментарии с ответами ----------


async def test_reply_to_comment(auth_client, second_client):
    client, _me = auth_client
    second = second_client
    other = (await second.get("/users/me")).json()

    post = (await client.post("/posts/", json={"text": "обсуждаем"})).json()
    parent = (await client.post(f"/posts/{post['id']}/comments/", json={"text": "родитель"})).json()
    assert parent["parent_id"] is None
    assert parent["replies"] == []

    resp = await second.post(
        f"/posts/{post['id']}/comments/",
        json={"text": "ответ", "parent_id": parent["id"]},
    )
    assert resp.status_code == 201, resp.text
    reply = resp.json()
    assert reply["parent_id"] == parent["id"]
    assert reply["author"]["username"] == other["username"]

    # в детали поста ответ вложен в родителя, а не лежит в корне
    detail = (await client.get(f"/posts/{post['id']}")).json()["post"]
    assert detail["comments_count"] == 2
    assert len(detail["comments"]) == 1
    root = detail["comments"][0]
    assert root["id"] == parent["id"]
    assert len(root["replies"]) == 1
    assert root["replies"][0]["text"] == "ответ"


async def test_nested_replies_tree(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "ветка"})).json()

    root = (await client.post(f"/posts/{post['id']}/comments/", json={"text": "1"})).json()
    lvl2 = (
        await client.post(
            f"/posts/{post['id']}/comments/", json={"text": "2", "parent_id": root["id"]}
        )
    ).json()
    await client.post(f"/posts/{post['id']}/comments/", json={"text": "3", "parent_id": lvl2["id"]})

    detail = (await client.get(f"/posts/{post['id']}")).json()["post"]
    assert detail["comments_count"] == 3
    # один корень, внутри два уровня вложенности
    assert len(detail["comments"]) == 1
    level2 = detail["comments"][0]["replies"]
    assert len(level2) == 1
    level3 = level2[0]["replies"]
    assert len(level3) == 1
    assert level3[0]["text"] == "3"


async def test_reply_to_missing_parent(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()
    resp = await client.post(
        f"/posts/{post['id']}/comments/", json={"text": "ответ", "parent_id": 999999}
    )
    assert resp.status_code == 404


async def test_reply_parent_must_belong_to_same_post(auth_client):
    client, _me = auth_client
    post_a = (await client.post("/posts/", json={"text": "пост A"})).json()
    post_b = (await client.post("/posts/", json={"text": "пост B"})).json()

    comment_on_a = (
        await client.post(f"/posts/{post_a['id']}/comments/", json={"text": "на A"})
    ).json()

    # нельзя «прицепить» ответ на комментарий из другого поста
    resp = await client.post(
        f"/posts/{post_b['id']}/comments/",
        json={"text": "нельзя", "parent_id": comment_on_a["id"]},
    )
    assert resp.status_code == 404


async def test_reply_requires_auth(anon_client, auth_client):
    authed, _me = auth_client
    post = (await authed.post("/posts/", json={"text": "пост"})).json()
    parent = (await authed.post(f"/posts/{post['id']}/comments/", json={"text": "p"})).json()

    resp = await anon_client.post(
        f"/posts/{post['id']}/comments/",
        json={"text": "аноним", "parent_id": parent["id"]},
    )
    assert resp.status_code == 401


async def test_deleting_parent_removes_replies(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()
    parent = (await client.post(f"/posts/{post['id']}/comments/", json={"text": "p"})).json()
    await client.post(
        f"/posts/{post['id']}/comments/", json={"text": "r1", "parent_id": parent["id"]}
    )
    await client.post(
        f"/posts/{post['id']}/comments/", json={"text": "r2", "parent_id": parent["id"]}
    )

    assert (await client.delete(f"/comments/{parent['id']}")).status_code == 204

    detail = (await client.get(f"/posts/{post['id']}")).json()["post"]
    assert detail["comments_count"] == 0
    assert detail["comments"] == []


async def test_delete_only_own_reply(auth_client, second_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()
    parent = (await client.post(f"/posts/{post['id']}/comments/", json={"text": "p"})).json()
    reply = (
        await second_client.post(
            f"/posts/{post['id']}/comments/",
            json={"text": "чужой ответ", "parent_id": parent["id"]},
        )
    ).json()

    # второй пользователь не может удалить корневой комментарий автора поста
    assert (await second_client.delete(f"/comments/{parent['id']}")).status_code == 403
    # но свой ответ — может
    assert (await second_client.delete(f"/comments/{reply['id']}")).status_code == 204


async def test_comment_counts_include_replies_in_feed(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "пост"})).json()
    parent = (await client.post(f"/posts/{post['id']}/comments/", json={"text": "p"})).json()
    await client.post(
        f"/posts/{post['id']}/comments/", json={"text": "r", "parent_id": parent["id"]}
    )

    resp = await client.get("/posts/")
    item = next(p for p in resp.json()["items"] if p["id"] == post["id"])
    assert item["comments_count"] == 2


# ---------- Приватные группы и членство ----------


async def test_create_private_group_makes_creator_member(auth_client):
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={
                "title": "Закрытая",
                "slug": "zakrytaya",
                "description": "",
                "is_private": True,
            },
        )
    ).json()
    assert group["is_private"] is True

    detail = (await client.get("/groups/zakrytaya/")).json()
    assert detail["group"]["is_private"] is True
    assert detail["group"]["is_member"] is True
    assert detail["group"]["members_count"] == 1


async def test_public_group_default_is_not_private(auth_client):
    client, _me = auth_client
    group = (await client.post("/groups/", json={"title": "Открытая", "slug": "otkrytaya"})).json()
    assert group["is_private"] is False


async def test_private_group_hidden_from_non_member(auth_client, second_client, anon_client):
    """Не-участник видит карточку группы, но НЕ её посты."""
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={"title": "Секрет", "slug": "sekret", "description": "", "is_private": True},
        )
    ).json()
    await client.post("/posts/", json={"text": "секретный пост", "group_id": group["id"]})

    resp = await second_client.get("/groups/sekret/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["group"]["is_member"] is False
    assert body["group"]["is_private"] is True
    assert body["posts"]["total"] == 0
    assert body["posts"]["items"] == []

    # аноним — так же
    resp = await anon_client.get("/groups/sekret/")
    assert resp.status_code == 200
    assert resp.json()["posts"]["items"] == []


async def test_private_group_visible_after_join(auth_client, second_client):
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={"title": "Секрет", "slug": "sekret2", "description": "", "is_private": True},
        )
    ).json()
    await client.post("/posts/", json={"text": "внутри", "group_id": group["id"]})

    # до вступления постов не видно
    before = (await second_client.get("/groups/sekret2/")).json()
    assert before["group"]["is_member"] is False
    assert before["posts"]["total"] == 0

    resp = await second_client.post("/groups/sekret2/join/")
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_member"] is True
    assert resp.json()["members_count"] == 2

    detail = (await second_client.get("/groups/sekret2/")).json()
    assert detail["group"]["is_member"] is True
    assert detail["posts"]["total"] == 1
    assert detail["posts"]["items"][0]["text"] == "внутри"


async def test_join_is_idempotent(auth_client, second_client):
    client, _me = auth_client
    await client.post(
        "/groups/",
        json={"title": "Г", "slug": "gruppa-idem", "description": "", "is_private": True},
    )

    await second_client.post("/groups/gruppa-idem/join/")
    resp = await second_client.post("/groups/gruppa-idem/join/")
    assert resp.json()["members_count"] == 2


async def test_leave_private_group(auth_client, second_client):
    client, _me = auth_client
    await client.post(
        "/groups/",
        json={"title": "Г", "slug": "gruppa-leave", "description": "", "is_private": True},
    )
    await second_client.post("/groups/gruppa-leave/join/")

    resp = await second_client.delete("/groups/gruppa-leave/leave/")
    assert resp.status_code == 200
    assert resp.json()["is_member"] is False
    assert resp.json()["members_count"] == 1

    # после выхода посты снова недоступны
    after = (await second_client.get("/groups/gruppa-leave/")).json()
    assert after["group"]["is_member"] is False
    assert after["posts"]["items"] == []


async def test_private_group_posts_hidden_from_global_feed(auth_client, second_client):
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={"title": "Приват", "slug": "privat-feed", "description": "", "is_private": True},
        )
    ).json()
    await client.post("/posts/", json={"text": "секрет", "group_id": group["id"]})
    await client.post("/posts/", json={"text": "обычный пост"})

    # не-участник видит только обычный пост
    resp = await second_client.get("/posts/")
    texts = [p["text"] for p in resp.json()["items"]]
    assert "секрет" not in texts
    assert "обычный пост" in texts

    # участник видит оба
    resp = await client.get("/posts/")
    texts = [p["text"] for p in resp.json()["items"]]
    assert "секрет" in texts


async def test_private_group_hidden_from_anon_feed(auth_client, anon_client):
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={"title": "Приват", "slug": "privat-anon", "description": "", "is_private": True},
        )
    ).json()
    await client.post("/posts/", json={"text": "секрет аноним", "group_id": group["id"]})

    resp = await anon_client.get("/posts/")
    texts = [p["text"] for p in resp.json()["items"]]
    assert "секрет аноним" not in texts


async def test_private_group_post_hidden_in_profile(auth_client, second_client):
    """Посты из приватной группы не видны в профиле постороннему."""
    client, me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={"title": "П", "slug": "privat-prof", "description": "", "is_private": True},
        )
    ).json()
    await client.post("/posts/", json={"text": "скрытый", "group_id": group["id"]})

    resp = await second_client.get(f"/profile/{me['username']}")
    assert resp.status_code == 200
    texts = [p["text"] for p in resp.json()["posts"]["items"]]
    assert "скрытый" not in texts


async def test_non_member_cannot_post_to_private_group(auth_client, second_client):
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={"title": "П", "slug": "privat-post", "description": "", "is_private": True},
        )
    ).json()

    resp = await second_client.post("/posts/", json={"text": "врываюсь", "group_id": group["id"]})
    assert resp.status_code == 403

    # участник может
    resp = await client.post("/posts/", json={"text": "нормально", "group_id": group["id"]})
    assert resp.status_code == 201


async def test_public_group_readable_by_anon(auth_client, anon_client):
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/", json={"title": "Откр", "slug": "publ-anon", "description": ""}
        )
    ).json()
    await client.post("/posts/", json={"text": "открытый", "group_id": group["id"]})

    resp = await anon_client.get("/groups/publ-anon/")
    assert resp.status_code == 200
    assert resp.json()["posts"]["total"] == 1
    assert resp.json()["group"]["is_member"] is False


async def test_join_requires_auth(anon_client, auth_client):
    authed, _me = auth_client
    await authed.post("/groups/", json={"title": "Г", "slug": "join-auth", "is_private": True})
    assert (await anon_client.post("/groups/join-auth/join/")).status_code == 401


async def test_join_missing_group(auth_client):
    client, _me = auth_client
    assert (await client.post("/groups/net-takoy/join/")).status_code == 404


async def test_private_flag_in_groups_list(auth_client):
    client, _me = auth_client
    await client.post("/groups/", json={"title": "П", "slug": "list-private", "is_private": True})
    await client.post("/groups/", json={"title": "О", "slug": "list-public"})

    groups = {g["slug"]: g for g in (await client.get("/groups/")).json()}
    assert groups["list-private"]["is_private"] is True
    assert groups["list-public"]["is_private"] is False


# ---------- Счётчики подписчиков ----------


async def test_profile_follower_counters(auth_client, second_client):
    client, _me = auth_client
    other = (await second_client.get("/users/me")).json()

    # изначально нули
    resp = await client.get(f"/profile/{other['username']}")
    assert resp.json()["followers_count"] == 0
    assert resp.json()["following_count"] == 0

    await client.post(f"/profile/{other['username']}/follow/")
    resp = await client.get(f"/profile/{other['username']}")
    assert resp.json()["followers_count"] == 1
    assert resp.json()["following_count"] == 0

    # у подписчика наоборот
    resp = await client.get("/profile/me")
    assert resp.json()["following_count"] == 1
    assert resp.json()["followers_count"] == 0


async def test_followers_count_decreases_on_unfollow(auth_client, second_client):
    client, _me = auth_client
    other = (await second_client.get("/users/me")).json()

    await client.post(f"/profile/{other['username']}/follow/")
    assert (await client.get(f"/profile/{other['username']}")).json()["followers_count"] == 1

    await client.delete(f"/profile/{other['username']}/follow/")
    assert (await client.get(f"/profile/{other['username']}")).json()["followers_count"] == 0


async def test_profile_counters_for_anonymous(anon_client, auth_client):
    """Аноним видит счётчики подписок, но is_following всегда False."""
    _authed, me = auth_client
    resp = await anon_client.get(f"/profile/{me['username']}")
    assert resp.status_code == 200
    assert "followers_count" in resp.json()
    assert "following_count" in resp.json()
    assert resp.json()["is_following"] is False
