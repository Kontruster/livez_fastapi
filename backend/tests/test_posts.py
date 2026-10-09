"""Тесты постов, ленты, пагинации, поиска и прав."""

import pytest

pytestmark = pytest.mark.asyncio


async def test_feed_empty(client):
    resp = await client.get("/posts/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_create_post_requires_auth(client):
    resp = await client.post("/posts/", json={"text": "аноним"})
    assert resp.status_code == 401


async def test_create_and_read_post(auth_client):
    client, me = auth_client

    resp = await client.post("/posts/", json={"text": "Привет, LiveZ!"})
    assert resp.status_code == 201, resp.text
    post = resp.json()
    assert post["text"] == "Привет, LiveZ!"
    assert post["author"]["username"] == me["username"]
    assert post["comments_count"] == 0
    assert post["images"] == []
    assert "title" not in post

    resp = await client.get(f"/posts/{post['id']}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["post"]["id"] == post["id"]
    assert detail["author_post_count"] == 1


async def test_create_post_empty_text_rejected(auth_client):
    client, _me = auth_client
    resp = await client.post("/posts/", json={"text": "   "})
    assert resp.status_code == 422


async def test_post_not_found(client):
    resp = await client.get("/posts/999999")
    assert resp.status_code == 404


async def test_edit_post_by_author(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "старый текст"})).json()

    resp = await client.patch(f"/posts/{post['id']}/", json={"text": "новый текст"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["text"] == "новый текст"


async def test_edit_post_partial_keeps_text(auth_client):
    """PATCH без text не должен затирать текст."""
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "не трогать"})).json()

    resp = await client.patch(f"/posts/{post['id']}/", json={})
    assert resp.status_code == 200, resp.text
    assert resp.json()["text"] == "не трогать"


async def test_edit_foreign_post_forbidden(auth_client, second_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "мой пост"})).json()

    resp = await second_client.patch(f"/posts/{post['id']}/", json={"text": "взлом"})
    assert resp.status_code == 403


async def test_delete_post_by_author(auth_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "удалить меня"})).json()

    resp = await client.delete(f"/posts/{post['id']}")
    assert resp.status_code == 204

    assert (await client.get(f"/posts/{post['id']}")).status_code == 404


async def test_delete_foreign_post_forbidden(auth_client, second_client):
    client, _me = auth_client
    post = (await client.post("/posts/", json={"text": "не твоё"})).json()

    resp = await second_client.delete(f"/posts/{post['id']}")
    assert resp.status_code == 403

    assert (await client.get(f"/posts/{post['id']}")).status_code == 200


async def test_feed_pagination(auth_client):
    client, _me = auth_client
    for i in range(12):
        resp = await client.post("/posts/", json={"text": f"пост номер {i}"})
        assert resp.status_code == 201, resp.text

    resp = await client.get("/posts/", params={"page": 1, "size": 5})
    assert resp.status_code == 200
    page1 = resp.json()
    assert len(page1["items"]) == 5
    assert page1["total"] == 12
    assert page1["pages"] == 3
    assert page1["page"] == 1

    resp = await client.get("/posts/", params={"page": 3, "size": 5})
    page3 = resp.json()
    assert len(page3["items"]) == 2
    assert page3["page"] == 3

    ids1 = {p["id"] for p in page1["items"]}
    ids3 = {p["id"] for p in page3["items"]}
    assert ids1.isdisjoint(ids3)


async def test_feed_search(auth_client):
    client, _me = auth_client
    await client.post("/posts/", json={"text": "уникальное слово зебра"})
    await client.post("/posts/", json={"text": "совсем другой текст"})

    resp = await client.get("/posts/", params={"q": "зебра"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert "зебра" in body["items"][0]["text"]


async def test_feed_search_no_match(auth_client):
    client, _me = auth_client
    await client.post("/posts/", json={"text": "обычный пост"})

    resp = await client.get("/posts/", params={"q": "неттакогослова"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_feed_ordering_newest_first(auth_client):
    client, _me = auth_client
    first = (await client.post("/posts/", json={"text": "первый"})).json()
    second = (await client.post("/posts/", json={"text": "второй"})).json()

    resp = await client.get("/posts/")
    ids = [p["id"] for p in resp.json()["items"]]
    assert ids.index(second["id"]) < ids.index(first["id"])


async def test_feed_includes_group(auth_client):
    client, _me = auth_client
    group = (
        await client.post(
            "/groups/",
            json={"title": "Тестовая", "slug": "testovaya", "description": "d"},
        )
    ).json()

    post = (await client.post("/posts/", json={"text": "в группе", "group_id": group["id"]})).json()
    assert post["group"]["slug"] == "testovaya"

    resp = await client.get("/posts/")
    item = next(p for p in resp.json()["items"] if p["id"] == post["id"])
    assert item["group"]["id"] == group["id"]


async def test_create_post_in_missing_group(auth_client):
    client, _me = auth_client
    resp = await client.post("/posts/", json={"text": "пост", "group_id": 999999})
    assert resp.status_code == 404
