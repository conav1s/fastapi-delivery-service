import httpx

PACKAGE_TYPES = [
    {"id": 1, "name": "Одежда"},
    {"id": 2, "name": "Электроника"},
    {"id": 3, "name": "Разное"},
]


async def test_list_package_types(client: httpx.AsyncClient) -> None:
    response = await client.get("/package-types")

    assert response.status_code == 200
    assert response.json() == PACKAGE_TYPES
