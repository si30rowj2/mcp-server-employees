"""
従業員情報 MCP サーバー ユニットテスト

実際の data/employees.db に対してツール関数を実行し、結果を検証する。
"""

import json

import pytest

from src.server import (
    get_direct_reports,
    get_management_chain,
    list_departments,
    lookup_employee,
    search_employees,
)


@pytest.mark.asyncio
async def test_lookup_employee_exact():
    """従業員 ID で正しい 1 名が返る。"""
    result = json.loads(await lookup_employee("E0001"))
    assert result is not None
    assert result["employee_id"] == "E0001"
    assert result["last_name"] == "田中"
    assert result["first_name"] == "愛子"
    assert result["full_name"] == "田中愛子"
    assert result["department"] == "経営企画部"
    # 社長は上長を持たない
    assert result["manager_id"] is None
    assert result["manager_name"] is None


@pytest.mark.asyncio
async def test_lookup_employee_includes_manager_name():
    """上長を持つ従業員には manager_name が付与される。"""
    result = json.loads(await lookup_employee("E0006"))
    assert result["manager_id"] == "E0002"
    assert result["manager_name"] == "佐藤健二"


@pytest.mark.asyncio
async def test_lookup_employee_id_normalized():
    """小文字・数字のみの ID でも同じ結果になる。"""
    lower = json.loads(await lookup_employee("e0001"))
    numeric = json.loads(await lookup_employee("1"))
    canonical = json.loads(await lookup_employee("E0001"))
    assert lower == canonical
    assert numeric == canonical


@pytest.mark.asyncio
async def test_lookup_employee_not_found():
    """存在しない ID は null を返す。"""
    assert json.loads(await lookup_employee("E9999")) is None
    assert json.loads(await lookup_employee("")) is None


@pytest.mark.asyncio
async def test_search_employees_keyword():
    """氏名キーワードで従業員が引ける。"""
    result = json.loads(await search_employees(query="田中"))
    assert len(result) > 0
    assert any(r["full_name"] == "田中愛子" for r in result)


@pytest.mark.asyncio
async def test_search_employees_department_filter():
    """部署で絞り込める。"""
    result = json.loads(await search_employees(department="開発部"))
    assert len(result) > 0
    assert all(r["department"] == "開発部" for r in result)


@pytest.mark.asyncio
async def test_search_employees_combined_filters():
    """キーワードと複数条件を組み合わせられる。"""
    result = json.loads(
        await search_employees(query="エンジニア", office_location="東京本社")
    )
    assert len(result) > 0
    assert all(r["office_location"] == "東京本社" for r in result)
    assert all("エンジニア" in r["job_title"] for r in result)


@pytest.mark.asyncio
async def test_search_employees_no_conditions_returns_all():
    """条件なしは limit 件まで全件返す。"""
    result = json.loads(await search_employees(limit=100))
    assert len(result) == 36


@pytest.mark.asyncio
async def test_list_departments():
    """部署一覧が人数付きで返る。"""
    result = json.loads(await list_departments())
    assert len(result) == 8
    total = sum(r["headcount"] for r in result)
    assert total == 36
    # 人数降順で並んでいる
    counts = [r["headcount"] for r in result]
    assert counts == sorted(counts, reverse=True)


@pytest.mark.asyncio
async def test_get_direct_reports():
    """直属の部下が返り、全員 manager_id が一致する。"""
    result = json.loads(await get_direct_reports("E0002"))
    assert len(result) > 0
    assert all(r["manager_id"] == "E0002" for r in result)


@pytest.mark.asyncio
async def test_get_direct_reports_none():
    """部下がいない従業員は空リストを返す。"""
    assert json.loads(await get_direct_reports("E0036")) == []


@pytest.mark.asyncio
async def test_get_management_chain():
    """上長チェーンが直属→上位の順にトップまで返る。"""
    result = json.loads(await get_management_chain("E0006"))
    ids = [r["employee_id"] for r in result]
    # E0006 -> 佐藤(E0002) -> 田中(E0001)
    assert ids == ["E0002", "E0001"]


@pytest.mark.asyncio
async def test_get_management_chain_top_is_empty():
    """最上位（社長）は上長を持たないため空リスト。"""
    assert json.loads(await get_management_chain("E0001")) == []
