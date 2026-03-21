import sqlite3

from ninja.testing import TestClient

from sqlite_viz.api import api


def test_list_tables(sqlite_db_file: str) -> None:
    client = TestClient(api)
    response = client.get(f"/tables?db_path={sqlite_db_file}")
    assert response.status_code == 200
    assert set(response.json()["tables"]) == {"users", "projects"}


def test_list_rows_returns_selectors(sqlite_db_file: str) -> None:
    client = TestClient(api)
    response = client.get(f"/tables/users/rows?db_path={sqlite_db_file}&limit=10&offset=0")
    assert response.status_code == 200
    payload = response.json()
    assert payload["table"] == "users"
    assert len(payload["rows"]) == 3
    assert len(payload["delete_selectors"]) == 3
    assert "id" in payload["delete_selectors"][0]["values"]


def test_bulk_delete_tables(sqlite_db_file: str) -> None:
    client = TestClient(api)
    response = client.delete("/tables", json={"db_path": sqlite_db_file, "tables": ["users", "projects"]})
    assert response.status_code == 200
    assert response.json()["deleted"] == 2

    conn = sqlite3.connect(sqlite_db_file)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
    }
    conn.close()
    assert tables == set()


def test_bulk_delete_rows(sqlite_db_file: str) -> None:
    client = TestClient(api)
    before = client.get(f"/tables/users/rows?db_path={sqlite_db_file}&limit=100&offset=0")
    selectors = before.json()["delete_selectors"][:2]

    response = client.delete(
        "/rows",
        json={"db_path": sqlite_db_file, "table": "users", "selectors": selectors},
    )
    assert response.status_code == 200
    assert response.json()["deleted"] == 2

    after = client.get(f"/tables/users/rows?db_path={sqlite_db_file}&limit=100&offset=0")
    assert len(after.json()["rows"]) == 1
