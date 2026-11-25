# -*- coding: utf-8 -*-
"""T2.2 续：mysql_params 三处去重 + 删 collaboration_db 空转 DDL"""
import io
import os
import re

ROOT = r"C:\Users\Administrator\Downloads\ai_learning_repo"

# ── 1. config.mysql_params 改为运行时读 env，删除仅被它使用的模块级常量 ──
p = os.path.join(ROOT, "data", "config.py")
src = io.open(p, encoding="utf-8").read()
old_consts = '''# MySQL 连接参数
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET", "utf8mb4")
'''
assert old_consts in src
src = src.replace(old_consts, "")
old_fn = '''def mysql_params() -> dict:
    """返回 PyMySQL 连接参数。"""
    return {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "charset": MYSQL_CHARSET,
        "autocommit": False,
    }'''
new_fn = '''def mysql_params() -> dict:
    """返回 PyMySQL 连接参数（唯一实现，调用时读 env）。"""
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "123456"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "autocommit": False,
    }'''
assert old_fn in src
src = src.replace(old_fn, new_fn)
io.open(p, "w", encoding="utf-8").write(src)
print("config.py: mysql_params now single source (dynamic env)")

# ── 2. dbapi.get_mysql_params 委托 config ──
p = os.path.join(ROOT, "data", "dbapi.py")
src = io.open(p, encoding="utf-8").read()
old_fn = '''def get_mysql_params() -> dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "123456"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "autocommit": False,
    }'''
new_fn = '''def get_mysql_params() -> dict[str, Any]:
    from data.config import mysql_params

    return mysql_params()'''
assert old_fn in src
src = src.replace(old_fn, new_fn)
io.open(p, "w", encoding="utf-8").write(src)
print("dbapi.py: get_mysql_params delegates to config")

# ── 3. migrate_to_mysql.py 同样委托 ──
p = os.path.join(ROOT, "scripts", "migrate_to_mysql.py")
src = io.open(p, encoding="utf-8").read()
m = re.search(r"(MYSQL_PARAMS\s*[:=][^\n]*\n(?:.*?\n)*?)\s*\"autocommit\": False,\s*\n\s*\}", src)
if m:
    old = m.group(0)
    new = "from data.config import mysql_params as _mysql_params\nMYSQL_PARAMS = _mysql_params()"
    # 保守：只替换字典字面量
    old_lit = re.search(r"\{[^{}]*\"autocommit\": False,\s*\n\s*\}", src)
    if old_lit and "MYSQL_HOST" in old_lit.group(0):
        src = src.replace(old_lit.group(0), "_mysql_params()")
        # 在其前插入导入（放文件头部导入区之后）
        anchor = src.find("\n\n")
        src = src[:anchor] + "\nfrom data.config import mysql_params as _mysql_params" + src[anchor:]
        io.open(p, "w", encoding="utf-8").write(src)
        print("migrate_to_mysql.py: params dict delegated to config")
    else:
        print("migrate_to_mysql.py: pattern not found, skipped")
else:
    print("migrate_to_mysql.py: MYSQL_PARAMS block not matched, skipped")

# ── 4. collaboration_db：删除 _init_tables（MySQL 下空转）──
p = os.path.join(ROOT, "data", "collaboration_db.py")
src = io.open(p, encoding="utf-8").read()
src = src.replace("        self._init_tables()\n", "")
i = src.find("    def _init_tables(self):")
assert i > 0
j = src.find("    # ═══════════════════════════════════════", i)
assert j > i
src = src[:i] + src[j:]
io.open(p, "w", encoding="utf-8").write(src)
print("collaboration_db.py: _init_tables removed,", len(src.splitlines()), "lines")
