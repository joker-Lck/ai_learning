# ── 构建阶段 ──
FROM python:3.11-slim AS builder

WORKDIR /app

# Debian APT 国内镜像源（deb.debian.org 在容器内不通）
RUN find /etc/apt -name "*.sources" -o -name "*.list" | xargs sed -i 's|deb.debian.org|mirrors.aliyun.com|g' 2>/dev/null; \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# pip 国内镜像加速
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --trusted-host mirrors.aliyun.com \
    -r requirements.txt

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

# Python 路径
ENV PYTHONPATH=/app

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
