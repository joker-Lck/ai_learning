"""
RAG 知识库数据库初始化脚本 - SQLite 版本
"""

import sqlite3
from data.config import get_rag_db_path


def init_rag_database():
    """初始化 RAG 知识库数据库"""
    try:
        db_path = get_rag_db_path()
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        cursor = conn.cursor()

        print("[INIT] 开始初始化 RAG 知识库数据库...")

        # 创建知识文档表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                file_path TEXT,
                file_type TEXT,
                file_size INTEGER DEFAULT 0,
                document_data TEXT,
                embedding TEXT,
                embedding_model TEXT DEFAULT 'spark-embedding',
                uploaded_by INTEGER,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                is_public INTEGER DEFAULT 1
            )
        """)
        print("  [OK] 知识文档表创建成功：knowledge_documents")

        # 创建 FTS5 虚拟表
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_documents_fts USING fts5(
                title, subject,
                content='knowledge_documents', content_rowid='id',
                tokenize='unicode61'
            )
        """)

        # 创建同步触发器
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS kd_fts_insert AFTER INSERT ON knowledge_documents BEGIN
                INSERT INTO knowledge_documents_fts(rowid, title, subject)
                VALUES (new.id, new.title, new.subject);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS kd_fts_delete AFTER DELETE ON knowledge_documents BEGIN
                INSERT INTO knowledge_documents_fts(knowledge_documents_fts, rowid, title, subject)
                VALUES ('delete', old.id, old.title, old.subject);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS kd_fts_update AFTER UPDATE ON knowledge_documents BEGIN
                INSERT INTO knowledge_documents_fts(knowledge_documents_fts, rowid, title, subject)
                VALUES ('delete', old.id, old.title, old.subject);
                INSERT INTO knowledge_documents_fts(rowid, title, subject)
                VALUES (new.id, new.title, new.subject);
            END
        """)
        print("  [OK] FTS5 全文索引创建成功")

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kd_subject ON knowledge_documents(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kd_upload_time ON knowledge_documents(upload_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kd_uploaded_by ON knowledge_documents(uploaded_by)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kd_usage_count ON knowledge_documents(usage_count)")

        # 创建知识点关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                point_name TEXT NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                UNIQUE(doc_id, point_name)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_kp_point_name ON knowledge_points(point_name)")
        print("  [OK] 知识点关联表创建成功：knowledge_points")

        # 创建文档分类表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL,
                parent_id INTEGER,
                subject TEXT,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (parent_id) REFERENCES document_categories(id) ON DELETE SET NULL,
                UNIQUE(category_name)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_parent ON document_categories(parent_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_subject ON document_categories(subject)")
        print("  [OK] 文档分类表创建成功：document_categories")

        # 插入基础学科分类数据
        cursor.executemany("""
            INSERT OR IGNORE INTO document_categories (category_name, subject, sort_order)
            VALUES (?, ?, ?)
        """, [
            ('语文', '语文', 1), ('数学', '数学', 2), ('英语', '英语', 3),
            ('物理', '物理', 4), ('化学', '化学', 5), ('生物', '生物', 6),
            ('历史', '历史', 7), ('地理', '地理', 8), ('政治', '政治', 9),
            ('体育', '体育', 10), ('美术', '美术', 11), ('音乐', '音乐', 12),
            ('信息技术', '信息技术', 13),
        ])
        print("  [OK] 基础学科分类数据插入成功")

        # 创建文档分类关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_category_relation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE CASCADE,
                UNIQUE(doc_id, category_id)
            )
        """)
        print("  [OK] 文档分类关联表创建成功")

        # 创建使用日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                user_id INTEGER,
                action_type TEXT,
                action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                search_keywords TEXT,
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_doc ON document_usage_log(doc_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_user ON document_usage_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_time ON document_usage_log(action_time)")
        print("  [OK] 使用日志表创建成功")

        conn.commit()
        print("\n[OK] RAG 知识库数据库初始化完成!")
        return True

    except Exception as e:
        print(f"\n[ERROR] RAG 知识库数据库初始化失败：{str(e)}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    success = init_rag_database()
    if success:
        print("\n[OK] RAG 知识库初始化成功！可以开始使用。")
    else:
        print("\n[ERROR] RAG 知识库初始化失败，请检查错误信息。")
