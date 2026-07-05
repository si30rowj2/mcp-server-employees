# 従業員情報 MCP サーバー

サンプルの従業員情報を格納したローカル SQLite データベースを、
Model Context Protocol (MCP) サーバーとして公開します。AI エージェントから
従業員の検索・組織構造の照会ができます。

## 概要

- データソース: `scripts/build_employees_db.py` で生成する `data/employees.db`（サンプル36名）
- REST API などの外部依存はなく、ローカル DB のみで完結
- トランスポート: **stdio**（ローカル）と **HTTP/SSE** の両対応

> **MCP クライアントの設定方法・ツールの詳しい使い方は [USAGE.md](USAGE.md) を参照してください。**
> Claude Desktop / VS Code などへの登録手順、各ツールのパラメータ、使用例をまとめています。

## 提供ツール

| ツール | 説明 |
| --- | --- |
| `lookup_employee(employee_id)` | 従業員 ID から 1 名の詳細を取得。ID は大文字小文字不問・数字のみでも補完（`"1"`→`"E0001"`）。上長名も付与。 |
| `search_employees(query="", department="", office_location="", employment_type="", status="", limit=50)` | 氏名・メール・電話・役職・部署を横断キーワード検索。部署／勤務地／雇用形態／在籍状況で絞り込み可。 |
| `list_departments()` | 部署ごとの在籍人数一覧（人数の多い順）。 |
| `get_direct_reports(manager_id)` | 指定従業員の直属の部下一覧（組織図のドリルダウン）。 |
| `get_management_chain(employee_id)` | 指定従業員の上長チェーン（直属の上長→最上位までのレポートライン）。 |

いずれのツールも結果を整形済み JSON 文字列で返します。

## データ項目（employees テーブル）

| カラム | 説明 |
| --- | --- |
| `employee_id` | 従業員 ID（主キー、例 `E0001`） |
| `first_name` / `last_name` | 名 / 姓（`full_name` に姓名結合を付与） |
| `email` / `phone` | メールアドレス（一意） / 電話番号 |
| `department` | 部署（例 `開発部`） |
| `job_title` | 役職（例 `バックエンドエンジニア`） |
| `employment_type` | 雇用形態（`正社員` / `契約社員` / `パートタイム` / `インターン`） |
| `office_location` | 勤務地（例 `東京本社`） |
| `hire_date` | 入社日（`YYYY-MM-DD`） |
| `manager_id` | 上長の従業員 ID（無い場合は `null`） |
| `status` | 在籍状況（例 `在籍中`） |

## 必要要件

- Python 3.10 以上
- pip

## セットアップ

```bash
# 仮想環境の作成・有効化
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 依存関係のインストール
pip install -r requirements.txt
```

## 実行方法

### 2 つのモードの違い（MCP をはじめて使う方へ）

このサーバーは、AI クライアント（Claude Desktop / VS Code など）と通信する方式（**トランスポート**）を
2 種類から選べます。**どちらもツールの機能は同じ**で、違いは「AI クライアントとどうつながるか」だけです。

- **stdio モード**: AI クライアントがこのサーバーを**子プロセスとして起動**し、標準入出力
  （キーボード入力・画面出力に使われるパイプ）を通じて 1 対 1 で会話します。
  ネットワークを一切使わないため、**同じ PC 上で使う**のが前提です。
- **HTTP/SSE モード**: このサーバーを**常駐する Web サーバーとして起動**しておき、AI クライアントが
  `http://…/sse` という URL 経由で接続します。ネットワーク越しに使えるため、**別の PC やコンテナ**
  からも接続でき、複数のクライアントで共有できます。

| 観点 | stdio モード | HTTP/SSE モード |
| --- | --- | --- |
| 起動する人 | AI クライアントが自動で起動 | 自分で先に起動しておく（常駐） |
| 通信経路 | 標準入出力（ネットワーク不使用） | HTTP（`http://localhost:38117/sse`） |
| 接続範囲 | 同じ PC 内のみ | 別 PC・コンテナからも可・複数接続可 |
| 設定の手間 | 少ない（コマンドを登録するだけ） | サーバーを起動＆URL を登録する |
| 向いている用途 | 手元の Claude Desktop などで手軽に使う | チーム共有・Docker・リモート運用 |

**迷ったら stdio モードを選んでください。** 手元の PC で Claude Desktop や VS Code から使うだけなら
stdio が最も簡単です。Docker で動かしたい、1 つのサーバーを複数人や複数ツールで共有したい、
別のマシンから接続したい、といった場合に HTTP/SSE モードを選びます。

### stdio モード（ローカル MCP クライアント向け）

```bash
python main.py --transport stdio
```

設定例は [examples/mcp-config-stdio.json](examples/mcp-config-stdio.json) を参照。

### HTTP/SSE モード

```bash
python main.py --transport sse
```

SSE エンドポイント: `http://localhost:38117/sse`
（ホスト・ポートは環境変数 `HTTP_HOST` / `HTTP_PORT` で変更可能）

## MCP クライアントの設定・使い方

MCP クライアント（Claude Desktop / VS Code など）への登録手順、各ツールの
パラメータ詳細、使用例は **[USAGE.md](USAGE.md)** にまとめています。主な内容:

- Claude Desktop への登録（stdio モード）: `claude_desktop_config.json` の設定例
- VS Code への登録（HTTP/SSE モード）: `.vscode/mcp.json` の設定例
- 各ツールのパラメータ表
- 環境変数（`.env`）・トラブルシューティング

設定例ファイルは [examples/mcp-config-stdio.json](examples/mcp-config-stdio.json) も参照できます。

## データベースの再構築

`data/employees.db` は同梱済みですが、サンプルデータから再構築するには:

```bash
python scripts/build_employees_db.py --db data/employees.db
```

スキーマ:

- `employees(employee_id, first_name, last_name, email, phone, department, job_title, employment_type, office_location, hire_date, manager_id, status)`
- `manager_id` は同テーブルの `employee_id` を参照する自己参照（組織構造）。

## テスト

```bash
pytest tests/ -v
```

## Docker

```bash
docker build -t employees-mcp-server .
docker run -p 48117:38117 employees-mcp-server
```

※ Docker の `CMD` は既定で SSE 起動しません。SSE で使う場合は
`CMD ["python", "main.py", "--transport", "sse"]` に変更してください。

### docker compose

`docker-compose.yml` で SSE 起動・DB マウント済みの構成を用意しています。

```bash
docker compose up -d
```

- **コンテナ内部ポートは `38117` 固定**（`HTTP_PORT`）、**ホスト公開ポートは `48117`** に
  マッピングしています（`ports: "48117:38117"`）。ホスト側からは
  `http://localhost:48117/sse` でアクセスします。公開ポートを変えたい場合は
  `docker-compose.yml` の `ports` の左側の番号を変更してください。
- `data/employees.db` は読み取り専用（`:ro`）でマウントされます。

## ライセンス

MIT
