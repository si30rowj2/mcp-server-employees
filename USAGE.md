# 従業員情報 MCP サーバー 使い方

## 概要

サンプルの従業員情報を格納したローカル SQLite データベース
（`data/employees.db`）を検索する MCP (Model Context Protocol) サーバーです。
外部 API に依存せず、ローカル DB のみで動作します。

## ツール

### `lookup_employee(employee_id)` — 従業員 ID から 1 名を取得

| パラメータ | 型 | 必須 | 既定 | 説明 |
|---|---|---|---|---|
| `employee_id` | str | ✓ | - | 従業員 ID。大文字小文字は不問。数字のみは補完（`"1"`→`"E0001"`）。 |

上長を持つ従業員には `manager_name`、氏名の姓名結合は `full_name` が付与されます。
該当がない場合は `null` を返します。

### `search_employees(query="", department="", office_location="", employment_type="", status="", limit=50)` — 従業員検索

| パラメータ | 型 | 必須 | 既定 | 説明 |
|---|---|---|---|---|
| `query` | str |  | "" | 氏名（姓・名・姓名結合）・メール・電話・役職・部署を横断する部分一致キーワード。 |
| `department` | str |  | "" | 部署名で完全一致絞り込み（例 `"開発部"`）。 |
| `office_location` | str |  | "" | 勤務地で完全一致絞り込み（例 `"東京本社"`）。 |
| `employment_type` | str |  | "" | 雇用形態で完全一致絞り込み（`"正社員"` / `"契約社員"` / `"パートタイム"` / `"インターン"`）。 |
| `status` | str |  | "" | 在籍状況で完全一致絞り込み（例 `"在籍中"`）。 |
| `limit` | int |  | 50 | 返す最大件数。 |

すべて省略した場合は全件を `limit` 件まで返します。

### `list_departments()` — 部署一覧

部署ごとの在籍人数（`department` / `headcount`）を人数の多い順で返します。

### `get_direct_reports(manager_id, limit=50)` — 直属の部下一覧

| パラメータ | 型 | 必須 | 既定 | 説明 |
|---|---|---|---|---|
| `manager_id` | str | ✓ | - | 上長側の従業員 ID（例 `"E0002"`）。数字のみでも補完。 |
| `limit` | int |  | 50 | 返す最大件数。 |

### `get_management_chain(employee_id)` — 上長チェーン

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `employee_id` | str | ✓ | 対象の従業員 ID（例 `"E0007"`）。数字のみでも補完。 |

直属の上長を先頭に、最上位（上長を持たない者）までを返します（本人は含めません）。

**戻り値:** いずれのツールも結果を整形済み JSON 文字列で返します。

## セットアップ

### 1. 仮想環境の作成

```powershell
python -m venv .venv
```

### 2. 依存関係のインストール

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 起動方法

### モード1: stdio トランスポート（標準入出力）

Claude Desktop などの MCP クライアントから直接起動される場合に使用します。

```powershell
.venv\Scripts\python.exe main.py --transport stdio
```

引数なしでも stdio がデフォルトです。

```powershell
.venv\Scripts\python.exe main.py
```

### モード2: HTTP/SSE トランスポート

HTTP 経由でアクセスしたい場合に使用します。

```powershell
.venv\Scripts\python.exe main.py --transport sse
```

または付属のバッチファイルを使用:

```cmd
examples\run-http-server.bat
```

SSE エンドポイント: `http://localhost:38117/sse`

## MCP クライアント設定

### Claude Desktop（stdio モード）

`%APPDATA%\Claude\claude_desktop_config.json` に以下を追加:

```json
{
  "mcpServers": {
    "employees": {
      "command": "C:\\data\\dev\\mcp-server-post-code\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\data\\dev\\mcp-server-post-code\\main.py",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

### VS Code（HTTP/SSE モード）

1. まず HTTP サーバーを起動:

```powershell
.venv\Scripts\python.exe main.py --transport sse
```

2. `.vscode/mcp.json` に以下を追加（VS Code は `url` 指定の SSE 接続に対応）:

```json
{
  "servers": {
    "employees-http": {
      "url": "http://localhost:38117/sse",
      "type": "sse"
    }
  }
}
```

> Docker Compose 経由で起動している場合、ホスト公開ポートは `48117` なので
> URL は `http://localhost:48117/sse` になります（`docker-compose.yml` の `ports` 設定）。

### Claude Desktop（HTTP/SSE モード）

Claude Desktop の設定ファイル（`claude_desktop_config.json`）は **stdio 起動のみ**対応で、
`url` / `transport` を直接指定して SSE サーバーへ接続することはできません。
HTTP/SSE サーバーへ繋ぐには、次のいずれかを使います。

**方法1: `mcp-remote` ブリッジ経由（設定ファイルで完結・推奨）**

`mcp-remote` が HTTP/SSE サーバーを stdio に橋渡しします（実行に Node.js / npx が必要）。
先に SSE サーバーを起動しておき、`%APPDATA%\Claude\claude_desktop_config.json` に追加:

```json
{
  "mcpServers": {
    "employees-http": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:38117/sse"]
    }
  }
}
```

> Docker Compose 経由の場合は URL を `http://localhost:48117/sse` にします。

**方法2: Connectors（カスタムコネクタ）から URL 登録**

Claude Desktop の「設定 → コネクタ → カスタムコネクタを追加」から、SSE サーバーの
URL（`http://localhost:38117/sse`）を直接登録できます（有料プラン向けの機能）。

> ローカル利用で最も手軽なのは、そもそも HTTP/SSE を使わず
> 前述の「Claude Desktop（stdio モード）」で登録する方法です。

**設定ファイルの場所:**

- **Claude Desktop**: `%APPDATA%\Claude\claude_desktop_config.json`
- **VS Code**: プロジェクトの `.vscode/mcp.json`

## 環境変数（オプション）

`.env` ファイルで設定をカスタマイズできます。

```env
# 従業員情報 SQLite DB のパス（省略時は data/employees.db）
# DB_PATH=data/employees.db

# HTTP サーバー設定（SSE モード用）
HTTP_HOST=0.0.0.0
HTTP_PORT=38117

# ログレベル
LOG_LEVEL=INFO
```

## テスト

```powershell
.venv\Scripts\python.exe -m pytest tests/ -v
```

## 使用例（Claude Desktop / GitHub Copilot）

MCP クライアントで以下のように依頼できます。

```
従業員 E0006 の情報を教えてください
開発部のエンジニアを一覧してください
E0002 の直属の部下は誰ですか
E0007 の上司をトップまでたどってください
部署ごとの人数を教えてください
```

MCP クライアントが自動的に `lookup_employee` / `search_employees` などのツールを呼び出します。

## データベースの再構築

サンプルデータから再構築するには:

```powershell
.venv\Scripts\python.exe scripts\build_employees_db.py --db data\employees.db
```

## トラブルシューティング

### HTTP モードでサーバーが起動しない

- ポート 38117 が既に使用されている可能性があります。`.env` で `HTTP_PORT` を変更してください。
- ファイアウォールでポートが許可されているか確認してください。

### MCP クライアントが接続できない

- HTTP モードの場合、サーバーが起動中か確認してください。
- URL が正しいか確認してください（`http://localhost:38117/sse`）。
- stdio モードの場合、パスが正しいか確認してください。

## ライセンス

MIT License
