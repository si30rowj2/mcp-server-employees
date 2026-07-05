# CLAUDE.md

このプロジェクトのコーディングルールは GitHub Copilot と共通化されています。
**共通ルールの正本は `.github/copilot-instructions.md`** です。以下でその内容を読み込みます。

@.github/copilot-instructions.md

---

## Claude Code 固有のメモ

- 上記の共通ルールに従うこと。ルールを更新する場合は、この `CLAUDE.md` ではなく
  `.github/copilot-instructions.md` を編集する（重複記載による更新漏れを防ぐため）。
- Windows / PowerShell 環境。仮想環境の有効化は `.venv\Scripts\activate`。
- DB アクセスは `src/employees_db.py`、MCP ツール定義は `src/server.py` に集約されている。
  変更前にこの 2 ファイルとレイヤリング方針を確認すること。
