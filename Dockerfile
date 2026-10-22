# ── 构建阶段 ──
FROM python:3.11-slim AS builder

WORKDIR /app

# 编译工具（pymilvus / scikit-network 等可能需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── 运行阶段 ──
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /install /usr/local

# ragas 0.4 + langchain-community>=0.4 兼容桩（VertexAI 模块已移除）
RUN SITE=$(python -c "import langchain_community, pathlib; print(pathlib.Path(langchain_community.__file__).parent)") && \
    printf '%s\n' \
      '"""Stub for removed VertexAI module (langchain-community>=0.4)."""' \
      '' \
      '' \
      'class ChatVertexAI:' \
      '    pass' \
      '' \
      '' \
      'class VertexAI:' \
      '    pass' \
      > "$SITE/chat_models/vertexai.py"

# 应用代码
COPY . .

# 运行时目录
RUN mkdir -p data/databases logs uploads exports

# 非 root 用户
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
