"""
数据库初始化脚本（MySQL 版本）

建库建表统一由 scripts/migrate_to_mysql.py 维护，
本脚本保持旧入口兼容（launcher.py 会调用它）。
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def main():
    from scripts.migrate_to_mysql import create_databases_and_tables, mysql_conn

    conn = mysql_conn()
    try:
        create_databases_and_tables(conn)
        print("[INIT] MySQL 数据库初始化完成")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
