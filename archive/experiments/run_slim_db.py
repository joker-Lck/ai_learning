# -*- coding: utf-8 -*-
"""T2.2 DB 层瘦身执行脚本"""
import io
import os
import re

ROOT = r"C:\Users\Administrator\Downloads\ai_learning_repo"

# ── 1. db_operations.py：删除零调用的领域 CRUD（用户/班级/学生/问题/学情）──
p = os.path.join(ROOT, "data", "db_operations.py")
src = io.open(p, encoding="utf-8").read()
start = src.find("    # ========== 用户相关操作 ==========")
end = src.find("# 创建全局数据库实例")
assert start > 0 and end > start, (start, end)
src = src[:start] + src[end:]
# 清理不再使用的 import
src = src.replace(
    "from core.logger import db_operation_failed, db_operation_success, debug, error",
    "from core.logger import db_operation_failed, debug, error",
)
src = src.replace("import json\nfrom data import dbapi as dbapi\nfrom datetime import datetime\n", "from data import dbapi as dbapi\n")
# 更新模块 docstring
src = src.replace(
    '"""MySQL 数据库操作模块（JSON 格式存储）\n提供数据库 CRUD 操作，所有复杂数据以 JSON 格式存储\n"""',
    '"""MySQL 数据库连接包装：Database 类与各库单例。\n领域 CRUD 见 data/dao.py（资源/测验/分析）与 services 各模块。\n"""',
)
io.open(p, "w", encoding="utf-8").write(src)
print("db_operations.py: trimmed to", len(src.splitlines()), "lines")

# ── 2. 删除 qa_db_operations.py（全仓零方法调用，仅 __init__ 导出）──
p2 = os.path.join(ROOT, "data", "qa_db_operations.py")
os.remove(p2)
print("qa_db_operations.py: deleted")

# ── 3. data/__init__.py：移除 qa_db 导出 ──
p3 = os.path.join(ROOT, "data", "__init__.py")
src3 = io.open(p3, encoding="utf-8").read()
src3 = src3.replace("from .qa_db_operations import qa_db\n", "")
src3 = src3.replace("    'qa_db',\n", "")
io.open(p3, "w", encoding="utf-8").write(src3)
print("data/__init__.py: qa_db export removed")

# ── 4. dbapi.get_mysql_params 与 config.mysql_params 去重 ──
p4 = os.path.join(ROOT, "data", "dbapi.py")
src4 = io.open(p4, encoding="utf-8").read()
m = re.search(r"def get_mysql_params\(\)[\s\S]*?(?=\n\ndef |\n\nclass )", src4)
print("dbapi.get_mysql_params block found:", bool(m))
if m:
    print("--- old block ---")
    print(m.group(0))
