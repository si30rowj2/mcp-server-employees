"""MCP server entrypoints and tool registration.

サンプル従業員情報 SQLite DB (data/employees.db) を MCP ツールとして公開する。
"""

import json
from typing import Literal

from mcp.server.fastmcp import FastMCP

from src import employees_db
from src.config import settings

mcp = FastMCP(
    "employees-server",
    instructions=(
        "This server provides tools for looking up and searching employee "
        "records (name, department, job title, office, reporting line) backed "
        "by a local SQLite database (data/employees.db)."
    ),
)

app = mcp.sse_app()


def _dump(data) -> str:
    """検索結果を整形済み JSON 文字列にする。"""
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
async def lookup_employee(employee_id: str) -> str:
    """従業員 ID から 1 名の詳細情報を取得する。

    Args:
        employee_id: 従業員 ID。大文字小文字は不問で、数字のみの場合は自動補完
            される（例 "E0001" / "e0001" / "1" はいずれも "E0001" として扱う）。

    Returns:
        従業員 1 名の詳細（氏名・メール・部署・役職・拠点・入社日・在籍状況ほか）を
        JSON 文字列で返す。上長の氏名は `manager_name`、氏名の姓名結合は `full_name`
        に含まれる。該当がない場合は ``null`` を返す。

    使用例:
        - "E0002 の従業員情報を教えて" -> lookup_employee("E0002")
    """
    return _dump(employees_db.get_employee(employee_id))


@mcp.tool()
async def search_employees(
    query: str = "",
    department: str = "",
    office_location: str = "",
    employment_type: str = "",
    status: str = "",
    limit: int = 50,
) -> str:
    """条件から従業員を検索する。

    Args:
        query: 氏名（姓・名・姓名結合）・メール・電話番号・役職・部署を横断して
            部分一致させるキーワード。省略時は絞り込み条件のみで検索する。
        department: 部署名で完全一致絞り込み（例 "開発部"）。省略可。
        office_location: 勤務地で完全一致絞り込み（例 "東京本社"）。省略可。
        employment_type: 雇用形態で完全一致絞り込み（例 "正社員" / "契約社員" /
            "パートタイム" / "インターン"）。省略可。
        status: 在籍状況で完全一致絞り込み（例 "在籍中"）。省略可。
        limit: 返す最大件数。

    Returns:
        条件に一致する従業員の一覧を JSON 文字列で返す。各要素には `full_name`
        （姓名結合）を含む。

    使用例:
        - "開発部のエンジニアを一覧して" -> search_employees(query="エンジニア", department="開発部")
        - "大阪支社の従業員" -> search_employees(office_location="大阪支社")
    """
    return _dump(
        employees_db.search_employees(
            query=query,
            department=department,
            office_location=office_location,
            employment_type=employment_type,
            status=status,
            limit=limit,
        )
    )


@mcp.tool()
async def list_departments() -> str:
    """部署ごとの在籍人数一覧を返す（部署マスタ相当）。

    Returns:
        部署名（`department`）と在籍人数（`headcount`）の一覧を、人数の多い順で
        JSON 文字列にして返す。

    使用例:
        - "部署ごとの人数を教えて" -> list_departments()
    """
    return _dump(employees_db.list_departments())


@mcp.tool()
async def get_direct_reports(manager_id: str, limit: int = 50) -> str:
    """指定した従業員の直属の部下一覧を返す（組織図のドリルダウン）。

    Args:
        manager_id: 上長側の従業員 ID（例 "E0002"）。数字のみでも補完される。
        limit: 返す最大件数。

    Returns:
        直属の部下（1 階層下）の従業員一覧を JSON 文字列で返す。部下がいない場合は
        空リストを返す。

    使用例:
        - "E0002 の部下は誰?" -> get_direct_reports("E0002")
    """
    return _dump(employees_db.get_direct_reports(manager_id, limit=limit))


@mcp.tool()
async def get_management_chain(employee_id: str) -> str:
    """指定した従業員の上長チェーン（レポートライン）を返す。

    Args:
        employee_id: 対象の従業員 ID（例 "E0007"）。数字のみでも補完される。

    Returns:
        直属の上長を先頭に、最上位（社長など上長を持たない者）までの上長一覧を
        JSON 文字列で返す。本人は含めない。上長がいない場合は空リストを返す。

    使用例:
        - "E0007 の上司をたどって" -> get_management_chain("E0007")
    """
    return _dump(employees_db.get_management_chain(employee_id))


def run_server(transport: Literal["stdio", "sse"] = "stdio") -> None:
    """Start the MCP server with the requested transport."""
    if transport == "sse":
        import uvicorn

        base_url = f"http://{settings.http_host}:{settings.http_port}"
        print(f"Starting MCP server with SSE transport on {base_url}")
        print(f"SSE endpoint: {base_url}/sse")

        uvicorn.run(
            mcp.sse_app(),
            host=settings.http_host,
            port=settings.http_port,
            log_level="info",
        )
    else:
        print("Starting MCP server with stdio transport")
        mcp.run()
