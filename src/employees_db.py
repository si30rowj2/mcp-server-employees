"""従業員情報 SQLite DB へのアクセス層。

data/employees.db を読み取り専用でオープンし、検索用の純粋関数を提供する。
server.py のツールから呼び出すほか、テストから直接実行できる。

SQL・DB アクセスはこのモジュールに集約する（server.py 側では SQL を書かない）。
"""

import sqlite3
from typing import Any, Optional

from src.config import settings

# employees テーブルから返すカラム（ツール応答の共通形）
_EMPLOYEE_COLUMNS = (
    "employee_id, first_name, last_name, email, phone, "
    "department, job_title, employment_type, office_location, "
    "hire_date, manager_id, status"
)

# 上長チェーンをたどる際の安全上限（循環参照・データ不整合への保険）
_MAX_CHAIN_DEPTH = 20


def _connect() -> sqlite3.Connection:
    """DB を読み取り専用でオープンする。"""
    conn = sqlite3.connect(
        f"file:{settings.db_path}?mode=ro",
        uri=True,
    )
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_employee(row: sqlite3.Row) -> dict[str, Any]:
    """行を従業員 dict に変換し、氏名の結合フィールドを付与する。"""
    data = dict(row)
    # 日本語の氏名表記（姓 + 名）。AI クライアントが扱いやすいよう明示的に付与する。
    data["full_name"] = f"{data['last_name']}{data['first_name']}"
    return data


def _rows_to_employees(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [_row_to_employee(row) for row in rows]


def normalize_employee_id(employee_id: str) -> str:
    """従業員 ID を正規化する。

    大文字化・前後空白除去を行い、数字のみが渡された場合は "E" + 4桁ゼロ埋め
    （例 "1" -> "E0001"）に補完する。空や不正な入力は空文字を返す。
    """
    value = (employee_id or "").strip().upper()
    if not value:
        return ""
    if value.isdigit():
        return "E" + value.zfill(4)
    return value


def get_employee(employee_id: str) -> Optional[dict[str, Any]]:
    """従業員 ID から 1 名の詳細を取得する（見つからなければ None）。

    上長（manager）の氏名を `manager_name` として付与する。
    """
    normalized = normalize_employee_id(employee_id)
    if not normalized:
        return None

    sql = (
        f"SELECT {_prefixed('e')}, "
        "m.last_name AS _mgr_last, m.first_name AS _mgr_first "
        "FROM employees e "
        "LEFT JOIN employees m ON e.manager_id = m.employee_id "
        "WHERE e.employee_id = ?"
    )
    with _connect() as conn:
        row = conn.execute(sql, (normalized,)).fetchone()
    if row is None:
        return None

    data = dict(row)
    mgr_last = data.pop("_mgr_last", None)
    mgr_first = data.pop("_mgr_first", None)
    employee = _row_to_employee_from_dict(data)
    employee["manager_name"] = (
        f"{mgr_last}{mgr_first}" if mgr_last is not None else None
    )
    return employee


def search_employees(
    query: str = "",
    department: str = "",
    office_location: str = "",
    employment_type: str = "",
    status: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """条件に一致する従業員を検索する。

    query は氏名（姓・名・姓名結合）・メール・電話・役職・部署を横断して部分一致
    させる。department / office_location / employment_type / status はそれぞれ完全
    一致で絞り込む（空文字は無視）。すべて空の場合は全件を（limit 件まで）返す。
    """
    conditions: list[str] = []
    params: list[Any] = []

    query = (query or "").strip()
    if query:
        like = f"%{query}%"
        conditions.append(
            "("
            "last_name LIKE ? OR first_name LIKE ? "
            "OR (last_name || first_name) LIKE ? "
            "OR email LIKE ? OR phone LIKE ? "
            "OR job_title LIKE ? OR department LIKE ?"
            ")"
        )
        params.extend([like, like, like, like, like, like, like])

    for column, value in (
        ("department", department),
        ("office_location", office_location),
        ("employment_type", employment_type),
        ("status", status),
    ):
        value = (value or "").strip()
        if value:
            conditions.append(f"{column} = ?")
            params.append(value)

    where = f"WHERE {' AND '.join(conditions)} " if conditions else ""
    sql = (
        f"SELECT {_EMPLOYEE_COLUMNS} FROM employees "
        f"{where}"
        "ORDER BY employee_id "
        "LIMIT ?"
    )
    params.append(limit)

    with _connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return _rows_to_employees(rows)


def list_departments() -> list[dict[str, Any]]:
    """部署ごとの在籍人数一覧を返す（部署マスタ相当）。"""
    sql = (
        "SELECT department, COUNT(*) AS headcount "
        "FROM employees "
        "GROUP BY department "
        "ORDER BY headcount DESC, department"
    )
    with _connect() as conn:
        rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def get_direct_reports(manager_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """指定した従業員の直属の部下一覧を返す（組織図のドリルダウン）。"""
    normalized = normalize_employee_id(manager_id)
    if not normalized:
        return []

    sql = (
        f"SELECT {_EMPLOYEE_COLUMNS} FROM employees "
        "WHERE manager_id = ? "
        "ORDER BY employee_id "
        "LIMIT ?"
    )
    with _connect() as conn:
        rows = conn.execute(sql, (normalized, limit)).fetchall()
    return _rows_to_employees(rows)


def get_management_chain(employee_id: str) -> list[dict[str, Any]]:
    """指定従業員の上長チェーンを、直属の上長から上位へ順に返す。

    本人は含めず、直属の上長を先頭に、最上位（社長など manager_id が無い者）まで
    たどる。循環参照や深すぎる階層に備え上限を設ける。従業員が存在しない、または
    上長がいない場合は空リストを返す。
    """
    normalized = normalize_employee_id(employee_id)
    if not normalized:
        return []

    chain: list[dict[str, Any]] = []
    visited: set[str] = {normalized}
    current = normalized

    sql = f"SELECT {_EMPLOYEE_COLUMNS} FROM employees WHERE employee_id = ?"
    with _connect() as conn:
        for _ in range(_MAX_CHAIN_DEPTH):
            row = conn.execute(sql, (current,)).fetchone()
            if row is None:
                break
            manager_id = row["manager_id"]
            if not manager_id or manager_id in visited:
                break
            manager_row = conn.execute(sql, (manager_id,)).fetchone()
            if manager_row is None:
                break
            chain.append(_row_to_employee(manager_row))
            visited.add(manager_id)
            current = manager_id

    return chain


# --- 内部ヘルパー -----------------------------------------------------------


def _prefixed(alias: str) -> str:
    """テーブル別名付きの従業員カラム列を生成する（JOIN 用）。"""
    return ", ".join(f"{alias}.{col.strip()}" for col in _EMPLOYEE_COLUMNS.split(","))


def _row_to_employee_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """dict 化済みの行に氏名結合フィールドを付与する。"""
    data["full_name"] = f"{data['last_name']}{data['first_name']}"
    return data
