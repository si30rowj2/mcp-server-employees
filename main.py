"""
従業員情報検索 MCP サーバー - エントリーポイント
"""

import sys
import os
import argparse

# プロジェクトルートを Python パスに追加
sys.path.insert(0, os.path.dirname(__file__))

from src.server import run_server

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="従業員情報検索 MCP サーバー")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="トランスポート方式: stdio (標準入出力) または sse (HTTP/SSE)",
    )
    args = parser.parse_args()

    run_server(transport=args.transport)
