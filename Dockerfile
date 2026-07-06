# Python 3.13 ベースイメージを使用（3.10 以上の要件を満たす）
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なツールのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python の依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ログディレクトリを作成
RUN mkdir -p logs

# 非 root ユーザーを作成して実行
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# ポート 38117 を公開
EXPOSE 38117

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:38117/health')"

# アプリケーションを起動
CMD ["python", "main.py"]
