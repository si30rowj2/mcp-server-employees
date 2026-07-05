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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
