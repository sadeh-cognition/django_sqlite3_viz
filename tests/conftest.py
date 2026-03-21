import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def sqlite_db_file(tmp_path: Path) -> str:
    db_path = tmp_path / "sample.sqlite3"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
    conn.execute("CREATE TABLE projects (id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
    conn.executemany("INSERT INTO users (name) VALUES (?)", [("Ada",), ("Linus",), ("Grace",)])
    conn.executemany("INSERT INTO projects (title) VALUES (?)", [("A",), ("B",)])
    conn.commit()
    conn.close()
    return str(db_path)
