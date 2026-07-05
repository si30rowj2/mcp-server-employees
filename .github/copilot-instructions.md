# コーディングルール（共通）

> このファイルはプロジェクト共通のコーディングルールの **正本（Single Source of Truth）** です。
> GitHub Copilot はこのファイルを自動で読み込みます。Claude Code は `CLAUDE.md` 経由でこのファイルを読み込みます。
> **ルールを変更するときは必ずこのファイルを編集してください**（`CLAUDE.md` 側には共通ルールを重複記載しない）。

## プロジェクト概要

サンプルの従業員情報を格納したローカル SQLite DB を、Model Context Protocol (MCP)
サーバーとして公開する Python プロジェクト。外部 API 依存はなくローカル DB のみで完結する。
トランスポートは **stdio**（ローカル）と **HTTP/SSE** の両対応。

提供ツール: `lookup_employee` / `search_employees` / `list_departments` /
`get_direct_reports` / `get_management_chain`

## 技術スタック

- **言語**: Python 3.10 以上
- **MCP**: `mcp`（FastMCP）
- **設定**: `pydantic` / `pydantic-settings`（`.env` から読み込み）
- **HTTP**: `fastapi` + `uvicorn`（SSE トランスポート用）
- **DB**: 標準ライブラリ `sqlite3`（`data/employees.db`）
- **ログ**: `loguru`
- **テスト**: `pytest` + `pytest-asyncio`
- **整形/静的解析**: `black` / `flake8` / `mypy`

## ディレクトリ構成

```
main.py                        エントリーポイント（--transport stdio|sse）
src/
  server.py                    MCP サーバー定義・ツール登録（FastMCP）
  employees_db.py              SQLite アクセス層（DB クエリはここに集約）
  config.py                    設定（pydantic-settings / .env）
  logging_config.py            ロギング設定
scripts/build_employees_db.py  サンプル従業員 DB を再構築
tests/                         pytest（実 DB に対して実行）
data/employees.db              従業員情報 SQLite DB（同梱・生成物）
```

## コーディング規約

### スタイル

- フォーマッタは **black**（コミット前に必ず実行。行長は black 既定の 88）。
- **flake8** / **mypy** の警告は解消してからコミットする。
- インポートは「標準ライブラリ → サードパーティ → ローカル（`src.*`）」の順にグループ分けし、
  グループ間は空行で区切る。
- 型ヒントは公開関数・メソッドの引数と戻り値に必ず付ける（`typing` を活用）。

### 命名

- モジュール/関数/変数は `snake_case`、クラスは `PascalCase`、定数は `UPPER_SNAKE_CASE`。
- モジュール内部専用のヘルパーは先頭アンダースコア（例: `_dump`, `_PROJECT_ROOT`）。

### ドキュメンテーション

- すべての公開モジュール・関数・クラスに docstring を書く。
- **docstring・コメントは日本語**で記述する（既存コードに合わせる）。MCP ツールの docstring は
  そのまま AI 向けの説明になるため、引数・戻り値・使用例を丁寧に書く（`Args:` / `Returns:` を含める）。

### レイヤリング（重要）

- **SQL・DB アクセスは `src/employees_db.py` に集約**する。`server.py` のツール関数から
  直接 SQL を書かない。
- MCP ツールは `src/server.py` に `@mcp.tool()` で登録する。ツール関数は **`async def`** で定義し、
  戻り値は **JSON 文字列**とする。整形は共通ヘルパー `_dump()` を使い、日本語を壊さないよう
  必ず `json.dumps(..., ensure_ascii=False)` 相当で出力する。
- 設定値はハードコードせず `src/config.py` の `settings` から取得する。新しい設定は `Settings`
  クラスに型付きで追加し、`.env.example` にも項目を追記する。

### エラーハンドリング

- 想定される入力エラー（存在しない従業員 ID など）は例外を投げずに、空リストや `null` など
  説明的な結果として返すことを検討する（AI クライアントが解釈しやすい形にする）。
- ログ出力は `print` ではなく `loguru` を使う。

## テスト

- テストは `tests/` に置き、`pytest` + `pytest-asyncio` で記述する。
- 非同期のツール関数をテストする際は `@pytest.mark.asyncio` を付け、`await` で呼び出して
  JSON をパースし検証する（`tests/test_server.py` を参照）。
- ツールの入出力に関わる変更を行ったら、対応するテストを追加・更新する。

## よく使うコマンド

```bash
# 仮想環境（Windows）
python -m venv .venv
.venv\Scripts\activate

# 依存関係
pip install -r requirements.txt

# 起動
python main.py --transport stdio      # ローカル MCP クライアント向け
python main.py --transport sse        # HTTP/SSE（既定 http://localhost:38117/sse）

# テスト / 整形 / 静的解析
pytest
black .
flake8 .
mypy src
```

## やってはいけないこと

- `.env`・`.venv/`・`logs/`・`__pycache__/`・`.pytest_cache/` をコミットしない（`.gitignore` 済み）。
- `data/employees.db` を手作業で書き換えない。再構築は `scripts/build_employees_db.py` 経由で行う。
- 従業員情報の検索・参照のために、SQLite データベース（`data/employees.db`）をスクリプトや
  sqlite3 CLI などで直接検索しない。AI エージェントや MCP クライアントからの検索・参照は、
  必ず MCP サーバーの提供ツール（`lookup_employee` / `search_employees` など）経由で行う。
- MCPサーバに問い合わせする場合は、このプロジェクトのソースを直接参照はしない。必ずMCPサーバの提供するツールを経由すること。(直接ソースを参照するとMCPの意味がないため)
- 秘密情報をコードに直書きしない（`.env` と `settings` で扱う）。
- 既存の日本語コメント/docstring を英語に置き換えない。
