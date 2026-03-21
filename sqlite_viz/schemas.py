from ninja import Schema


class TableListResponse(Schema):
    tables: list[str]


class RowDeleteSelector(Schema):
    values: dict[str, str | int | float | None]


class TableRowsResponse(Schema):
    table: str
    columns: list[str]
    rows: list[dict]
    delete_selectors: list[RowDeleteSelector]


class DeleteTablesRequest(Schema):
    db_path: str
    tables: list[str]


class DeleteRowsRequest(Schema):
    db_path: str
    table: str
    selectors: list[RowDeleteSelector]


class DeleteResultResponse(Schema):
    deleted: int
