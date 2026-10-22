"""
RAG 知识库初始化脚本（MySQL 版本）

表结构由 scripts/migrate_to_mysql.py 统一维护。
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
        print("[INIT] ai_rag_knowledge 初始化完成")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
