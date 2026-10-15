from decimal import Decimal
from typing import Any

import httpx

from delivery_service.config import settings

from .conftest import ClientFactory, CostServiceInstaller

TEST_PACKAGE = {
    "name": "Laptop",
    "type_id": 2,
    "weight": "42",
    "content_cost_usd": "4242",
}


async def test_create_package_return_id_and_sets_session_cookie(client: httpx.AsyncClient) -> None:
    response = await client.post("/packages", json=TEST_PACKAGE)

    assert response.status_code == 201
    assert response.json()["package_id"] > 0
    assert settings.session.name in response.cookies


async def create_package(client: httpx.AsyncClient, **overrides: dict[str, Any]) -> int:
    response = await client.post("/packages", json=TEST_PACKAGE | overrides)
    assert response.status_code == 201, response.text
    return int(response.json()["package_id"])


async def test_new_package_has_no_delivery_cost(client: httpx.AsyncClient) -> None:
    package_id = await create_package(client)

    response = await client.get(f"/packages/{package_id}")

    assert response.status_code == 200
    assert response.json()["delivery_cost_rub"] == "Не рассчитано"


async def test_foreign_package_is_not_found(make_client: ClientFactory) -> None:
    owner, stranger = make_client(), make_client()
    package_id = await create_package(owner)

    response = await stranger.get(f"/packages/{package_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "package_not_found"


async def test_unknown_package_type_is_rejected(client: httpx.AsyncClient) -> None:
    response = await client.post("/packages", json=TEST_PACKAGE | {"type_id": 999})

    assert response.status_code == 422
    assert response.json()["code"] == "package_type_not_found"


async def test_create_package_with_negative_weight(client: httpx.AsyncClient) -> None:
    response = await client.post("/packages", json=TEST_PACKAGE | {"weight": "-1"})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert response.json()["details"][0]["loc"] == ["body", "weight"]


async def test_fill_missing_costs_prices_package(
    client: httpx.AsyncClient, install_cost_service: CostServiceInstaller
) -> None:
    install_cost_service(Decimal("67"))
    package_id = await create_package(client)

    response = await client.post("/packages/fill-missing-costs")

    assert response.status_code == 200
    assert response.json() == {"updated": 1}

    package = (await client.get(f"/packages/{package_id}")).json()
    # (42 * 0.5 + 4242 * 0.01) * 67 = 4249.14
    assert package["delivery_cost_rub"] == "4249.14"


async def test_fill_missing_costs_without_rate(
    client: httpx.AsyncClient, install_cost_service: CostServiceInstaller
) -> None:
    install_cost_service(None)

    response = await client.post("/packages/fill-missing-costs")

    assert response.status_code == 503
    assert response.json()["code"] == "rate_unavailable"


async def test_package_lists_are_isolated_between_sessions(make_client: ClientFactory) -> None:
    other_client, another_client = make_client(), make_client()

    other_client_package_id = await create_package(other_client)
    await create_package(another_client)

    other_response = await other_client.get("/packages")
    another_response = await another_client.get("/packages")

    assert other_response.json()["total"] == 1
    assert another_response.json()["total"] == 1

    other_items = other_response.json()["items"]
    assert [item["id"] for item in other_items] == [other_client_package_id]


async def test_list_filters_by_type(client: httpx.AsyncClient) -> None:
    await create_package(client, type_id=2)
    await create_package(client, type_id=2)
    await create_package(client, type_id=3)

    response = await client.get("/packages", params={"type_id": 2})

    body = response.json()

    assert body["total"] == 2
    assert [item["type"]["id"] for item in body["items"]] == [2, 2]


async def test_list_filters_by_has_delivery_cost(
    client: httpx.AsyncClient, install_cost_service: CostServiceInstaller
) -> None:
    install_cost_service(Decimal("67"))

    priced_id1 = await create_package(client)
    priced_id2 = await create_package(client)

    response = await client.post("/packages/fill-missing-costs")
    assert response.json() == {"updated": 2}

    unpriced_id = await create_package(client)

    response = await client.get("/packages", params={"has_delivery_cost": True})
    body = response.json()

    assert body["total"] == 2
    assert [item["id"] for item in body["items"]] == [priced_id1, priced_id2]

    response = await client.get("/packages", params={"has_delivery_cost": False})
    body = response.json()

    assert body["total"] == 1
    assert [item["id"] for item in body["items"]] == [unpriced_id]


async def test_list_paginates_with_total_of_all_matches(client: httpx.AsyncClient) -> None:
    package_ids = [await create_package(client) for _ in range(5)]

    first_page = await client.get("/packages", params={"limit": 2, "offset": 0})
    second_page = await client.get("/packages", params={"limit": 2, "offset": 2})
    last_page = await client.get("/packages", params={"limit": 2, "offset": 4})

    for page in (first_page, second_page, last_page):
        assert page.status_code == 200, page.text
        # total counts every matching package, not just the ones on this page
        assert page.json()["total"] == 5

    assert first_page.json()["limit"] == 2
    assert second_page.json()["offset"] == 2

    def ids(page: httpx.Response) -> list[int]:
        return [item["id"] for item in page.json()["items"]]

    assert ids(first_page) == package_ids[0:2]
    assert ids(second_page) == package_ids[2:4]
    assert ids(last_page) == package_ids[4:5]


async def test_list_page_beyond_end_is_empty(client: httpx.AsyncClient) -> None:
    await create_package(client)

    response = await client.get("/packages", params={"limit": 2, "offset": 10})

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 1


async def test_list_rejects_limit_above_maximum(client: httpx.AsyncClient) -> None:
    response = await client.get("/packages", params={"limit": 101})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"
    assert response.json()["details"][0]["loc"] == ["query", "limit"]
