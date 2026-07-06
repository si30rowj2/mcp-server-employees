"""Application settings."""

import os

from pydantic_settings import BaseSettings

# プロジェクトルート（src/ の一つ上）。DB の既定パス解決に使う。
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    """Application settings."""

    log_level: str = "INFO"

    # 従業員情報 SQLite DB のパス
    db_path: str = os.path.join(_PROJECT_ROOT, "data", "employees.db")

    http_host: str = "0.0.0.0"
    http_port: int = 38117

    # DNS リバインディング保護で許可するホスト（カンマ区切り、ポートは ":*" 指定可）。
    # 空文字の場合は保護を無効化し、任意のホストからの SSE 接続を許可する。
    # 例: "192.168.3.68:*,localhost:*,127.0.0.1:*"
    allowed_hosts: str = ""

    # 上記の Origin 版（ブラウザクライアント向け。カンマ区切り）。
    # 例: "http://192.168.3.68:*,http://localhost:*"
    allowed_origins: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def allowed_hosts_list(self) -> list[str]:
        """`allowed_hosts` をカンマ区切りで分割したリストを返す。"""
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @property
    def allowed_origins_list(self) -> list[str]:
        """`allowed_origins` をカンマ区切りで分割したリストを返す。"""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
