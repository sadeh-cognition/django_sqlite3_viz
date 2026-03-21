from ninja import NinjaAPI, Query

from .schemas import (
    DeleteResultResponse,
    DeleteRowsRequest,
    DeleteTablesRequest,
    TableListResponse,
    TableRowsResponse,
)
from .services import SqliteVizError, delete_rows, delete_tables, list_rows, list_tables

api = NinjaAPI(urls_namespace="sqlite_viz_api")


@api.get("/tables", response=TableListResponse)
def get_tables(request, db_path: str = Query(...)) -> TableListResponse:
    try:
        tables = list_tables(db_path)
    except SqliteVizError as exc:
        return api.create_response(request, {"detail": str(exc)}, status=400)
    return TableListResponse(tables=tables)


@api.get("/tables/{table}/rows", response=TableRowsResponse)
def get_rows(
    request,
    table: str,
    db_path: str = Query(...),
    limit: int = Query(100),
    offset: int = Query(0),
) -> TableRowsResponse:
    try:
        columns, rows, selectors = list_rows(db_path=db_path, table=table, limit=limit, offset=offset)
    except (SqliteVizError, Exception) as exc:
        return api.create_response(request, {"detail": str(exc)}, status=400)
    return TableRowsResponse(table=table, columns=columns, rows=rows, delete_selectors=selectors)


@api.delete("/tables", response=DeleteResultResponse)
def remove_tables(request, payload: DeleteTablesRequest) -> DeleteResultResponse:
    try:
        deleted = delete_tables(db_path=payload.db_path, tables=payload.tables)
    except SqliteVizError as exc:
        return api.create_response(request, {"detail": str(exc)}, status=400)
    return DeleteResultResponse(deleted=deleted)


@api.delete("/rows", response=DeleteResultResponse)
def remove_rows(request, payload: DeleteRowsRequest) -> DeleteResultResponse:
    try:
        deleted = delete_rows(db_path=payload.db_path, table=payload.table, selectors=[s.dict() for s in payload.selectors])
    except (SqliteVizError, Exception) as exc:
        return api.create_response(request, {"detail": str(exc)}, status=400)
    return DeleteResultResponse(deleted=deleted)
