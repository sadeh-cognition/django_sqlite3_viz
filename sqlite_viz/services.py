import sqlite3
from pathlib import Path

MAX_LIMIT = 500


class SqliteVizError(ValueError):
    pass


def _validate_db_path(db_path: str) -> Path:
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        raise SqliteVizError(f"Database not found: {path}")
    return path


def browse_directory(path_str: str | None = None) -> tuple[str, str | None, list[dict]]:
    if not path_str:
        path = Path.cwd().resolve()
    else:
        path = Path(path_str).expanduser().resolve()
        if not path.exists():
            # If path doesn't exist, try its parent, or fallback to current directory
            parent = path.parent
            if parent.exists() and parent.is_dir():
                path = parent
            else:
                path = Path.cwd().resolve()
        elif not path.is_dir():
            # If it's a file, list its parent directory
            path = path.parent.resolve()

    # Determine parent path
    parent_path = str(path.parent.resolve()) if path != path.parent else None

    items: list[dict] = []
    try:
        for entry in path.iterdir():
            try:
                is_dir = entry.is_dir()
                size = None if is_dir else entry.stat().st_size
                items.append({
                    "name": entry.name,
                    "path": str(entry.resolve()),
                    "is_dir": is_dir,
                    "size": size,
                })
            except (PermissionError, FileNotFoundError):
                continue
    except PermissionError as exc:
        raise SqliteVizError(f"Permission denied: {path}") from exc

    # Sort: directories first, then files, both alphabetically
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

    return str(path), parent_path, items


def _quote_identifier(identifier: str) -> str:
    if not identifier:
        raise SqliteVizError("Identifier cannot be empty")
    safe = identifier.replace('"', '""')
    return f'"{safe}"'


def _get_connection(db_path: str) -> sqlite3.Connection:
    path = _validate_db_path(db_path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(db_path: str) -> list[str]:
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        return [row["name"] for row in rows]


def _table_primary_keys(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table)})").fetchall()
    return [row["name"] for row in rows if row["pk"] > 0]


def list_rows(db_path: str, table: str, limit: int = 100, offset: int = 0) -> tuple[list[str], list[dict], list[dict]]:
    safe_limit = max(1, min(limit, MAX_LIMIT))
    safe_offset = max(0, offset)
    with _get_connection(db_path) as conn:
        table_sql = _quote_identifier(table)
        pk_columns = _table_primary_keys(conn, table)
        selector_cols = pk_columns or ["rowid"]
        select_selector = ""
        if not pk_columns:
            select_selector = ", rowid"
        query = f"SELECT *{select_selector} FROM {table_sql} LIMIT ? OFFSET ?"
        rows = conn.execute(query, [safe_limit, safe_offset]).fetchall()
        if not rows:
            columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table_sql})").fetchall()]
            return columns, [], []

        row_keys = list(rows[0].keys())
        columns = row_keys if pk_columns else [k for k in row_keys if k != "rowid"]
        output_rows: list[dict] = []
        selectors: list[dict] = []
        
        def _format_value(val: object) -> object:
            if isinstance(val, bytes):
                return f"<BLOB: {len(val)} bytes>"
            return val
            
        for row in rows:
            as_dict = dict(row)
            output_rows.append({k: _format_value(as_dict[k]) for k in columns})
            selectors.append({"values": {col: _format_value(as_dict[col]) for col in selector_cols}})
        return columns, output_rows, selectors


def delete_tables(db_path: str, tables: list[str]) -> int:
    unique_tables = list(dict.fromkeys(tables))
    if not unique_tables:
        return 0
    with _get_connection(db_path) as conn:
        deleted = 0
        for table in unique_tables:
            conn.execute(f"DROP TABLE IF EXISTS {_quote_identifier(table)}")
            deleted += 1
        conn.commit()
        return deleted


def delete_rows(db_path: str, table: str, selectors: list[dict]) -> int:
    if not selectors:
        return 0
    with _get_connection(db_path) as conn:
        table_sql = _quote_identifier(table)
        deleted = 0
        for selector in selectors:
            selector_values = selector.get("values", {})
            if not selector_values:
                continue
            clauses = []
            values = []
            for key, value in selector_values.items():
                clauses.append(f"{_quote_identifier(key)} IS ?" if value is None else f"{_quote_identifier(key)} = ?")
                values.append(value)
            where = " AND ".join(clauses)
            cursor = conn.execute(f"DELETE FROM {table_sql} WHERE {where}", values)
            deleted += cursor.rowcount
        conn.commit()
        return deleted
