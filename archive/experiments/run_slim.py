# -*- coding: utf-8 -*-
"""执行瘦身：删除垃圾/死代码/空包，修复 BOM"""
import os
import shutil

ROOT = r"C:\Users\Administrator\Downloads\ai_learning_repo"

def rm(path, note):
    full = os.path.join(ROOT, path) if not os.path.isabs(path) else path
    if not os.path.exists(full):
        print(f"  SKIP (not found): {path}")
        return
    try:
        if os.path.isdir(full):
            shutil.rmtree(full)
        else:
            os.remove(full)
        print(f"  DELETED [{note}]: {path}")
    except Exception as e:
        print(f"  FAIL: {path} -> {e}")

print("== 1. 数据库与评测残留 ==")
for p in [
    "data/databases",            # 6 个测试库 (gitignored-ish / 可由 init_databases.py 重建)
    "data/retrieval_eval.db",    # 空 schema 评测库
    r"C:\Users\Administrator\.milvus\ai_learning.db",  # 损坏的 Milvus Lite 文件
]:
    rm(p, "db")

print("== 2. 缓存与日志 ==")
for p in [".pytest_cache", "logs", "data/__pycache__", "core/__pycache__", "tests/__pycache__", "services/__pycache__", "backend/__pycache__"]:
    rm(p, "cache")

print("== 3. 死代码（零引用）==")
for p in [
    "core/utils.py",
    "data/data_manager.py",
    "services/animation_service.py",
    "backend/config.py",         # 应用走 os.getenv，此 pydantic 配置仅测试引用
]:
    rm(p, "dead-code")

print("== 4. 空壳占位子包 ==")
for p in ["services/agents", "services/auth", "services/content", "services/retrieval"]:
    rm(p, "empty-pkg")

print("== 5. 临时分析脚本 ==")
for p in ["experiments/inspect_dbs.py", "experiments/inspect_docs.py", "experiments/inspect_docs2.py", "experiments/_sample_ch05.md"]:
    rm(p, "temp")

print("== 6. 修复 BOM ==")
for rel in ["data/db_operations.py", "data/qa_db_operations.py", "scripts/eval_retrieval.py"]:
    full = os.path.join(ROOT, rel)
    with open(full, "rb") as f:
        b = f.read()
    if b.startswith(b"\xef\xbb\xbf"):
        with open(full, "wb") as f:
            f.write(b[3:])
        print(f"  BOM removed: {rel}")
    else:
        print(f"  no BOM: {rel}")

print("done")
