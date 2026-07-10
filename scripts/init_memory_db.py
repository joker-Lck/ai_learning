"""
记忆系统初始化脚本 - SQLite 版本
支持短期记忆、情景记忆、语义记忆、实体记忆、遗忘机制、冲突修正
"""

import sqlite3
from data.config import get_memory_db_path


def init_memory_tables():
    """初始化记忆系统表结构"""
    db_path = get_memory_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    cursor = conn.cursor()

    try:
        print("\n[INIT] 初始化记忆数据库 (ai_memory)...")

        # 1. 短期记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant', 'system')) NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER DEFAULT 0,
                position INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stm_user_session ON short_term_memory(user_id, session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stm_created ON short_term_memory(created_at)")
        print("  [OK] 短期记忆表 (short_term_memory) 创建成功!")

        # 2. 情景记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                episode_type TEXT CHECK(episode_type IN ('conversation', 'learning', 'question', 'task', 'event')) NOT NULL,
                title TEXT,
                summary TEXT,
                context TEXT,
                content TEXT,
                emotions TEXT,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_em_user ON episodic_memory(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_em_type ON episodic_memory(episode_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_em_importance ON episodic_memory(importance)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_em_last_accessed ON episodic_memory(last_accessed_at)")

        # FTS5 虚拟表
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS episodic_memory_fts USING fts5(
                title, summary, content,
                content='episodic_memory', content_rowid='id',
                tokenize='unicode61'
            )
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS em_fts_insert AFTER INSERT ON episodic_memory BEGIN
                INSERT INTO episodic_memory_fts(rowid, title, summary, content)
                VALUES (new.id, new.title, new.summary, new.content);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS em_fts_delete AFTER DELETE ON episodic_memory BEGIN
                INSERT INTO episodic_memory_fts(episodic_memory_fts, rowid, title, summary, content)
                VALUES ('delete', old.id, old.title, old.summary, old.content);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS em_fts_update AFTER UPDATE ON episodic_memory BEGIN
                INSERT INTO episodic_memory_fts(episodic_memory_fts, rowid, title, summary, content)
                VALUES ('delete', old.id, old.title, old.summary, old.content);
                INSERT INTO episodic_memory_fts(rowid, title, summary, content)
                VALUES (new.id, new.title, new.summary, new.content);
            END
        """)
        print("  [OK] 情景记忆表 (episodic_memory) 创建成功!")

        # 3. 语义记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fact_type TEXT CHECK(fact_type IN ('preference', 'knowledge', 'skill', 'habit', 'goal', 'constraint')) NOT NULL,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                source TEXT,
                embedding BLOB,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                is_verified INTEGER DEFAULT 0,
                conflict_resolution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, subject, predicate, object)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sm_user ON semantic_memory(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sm_type ON semantic_memory(fact_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sm_subject ON semantic_memory(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sm_confidence ON semantic_memory(confidence)")
        print("  [OK] 语义记忆表 (semantic_memory) 创建成功!")

        # 4. 实体记忆表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entity_type TEXT CHECK(entity_type IN ('person', 'concept', 'skill', 'course', 'tool', 'organization', 'other')) NOT NULL,
                entity_name TEXT NOT NULL,
                entity_alias TEXT,
                attributes TEXT,
                description TEXT,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                embedding BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, entity_type, entity_name)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_user ON entity_memory(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_type ON entity_memory(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_name ON entity_memory(entity_name)")
        print("  [OK] 实体记忆表 (entity_memory) 创建成功!")

        # 5. 实体关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source_entity_id INTEGER NOT NULL,
                target_entity_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                relation_label TEXT,
                weight REAL DEFAULT 1.0,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, source_entity_id, target_entity_id, relation_type),
                FOREIGN KEY (source_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE,
                FOREIGN KEY (target_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_user ON entity_relations(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_source ON entity_relations(source_entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_target ON entity_relations(target_entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON entity_relations(relation_type)")
        print("  [OK] 实体关系表 (entity_relations) 创建成功!")

        # 6. 记忆元数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT CHECK(memory_type IN ('short_term', 'episodic', 'semantic', 'entity', 'relation')) NOT NULL,
                memory_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                importance REAL DEFAULT 0.5,
                decay_rate REAL DEFAULT 0.1,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                is_forgotten INTEGER DEFAULT 0,
                forgotten_at TIMESTAMP,
                reinforcement_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_type, memory_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_user ON memory_metadata(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_type ON memory_metadata(memory_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_forgotten ON memory_metadata(is_forgotten)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meta_importance ON memory_metadata(importance)")
        print("  [OK] 记忆元数据表 (memory_metadata) 创建成功!")

        # 7. 记忆冲突表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conflict_type TEXT CHECK(conflict_type IN ('fact_contradiction', 'preference_change', 'knowledge_update', 'temporal_conflict')) NOT NULL,
                old_memory_type TEXT NOT NULL,
                old_memory_id INTEGER NOT NULL,
                new_memory_type TEXT NOT NULL,
                new_memory_id INTEGER NOT NULL,
                resolution_strategy TEXT CHECK(resolution_strategy IN ('keep_old', 'keep_new', 'merge', 'manual')) DEFAULT 'manual',
                resolution_result TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_user ON memory_conflicts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_resolved ON memory_conflicts(resolved)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conflict_type ON memory_conflicts(conflict_type)")
        print("  [OK] 记忆冲突表 (memory_conflicts) 创建成功!")

        # 8. 记忆访问日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                memory_type TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                access_type TEXT CHECK(access_type IN ('read', 'write', 'reinforce', 'forget')) NOT NULL,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_user ON memory_access_log(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_memory ON memory_access_log(memory_type, memory_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_access_created ON memory_access_log(created_at)")
        print("  [OK] 记忆访问日志表 (memory_access_log) 创建成功!")

        # 为需要 updated_at 的表添加触发器
        for table in ['episodic_memory', 'semantic_memory', 'entity_memory', 'entity_relations', 'memory_metadata']:
            cursor.execute(f"""
                CREATE TRIGGER IF NOT EXISTS trg_{table}_updated_at
                AFTER UPDATE ON {table}
                FOR EACH ROW
                BEGIN
                    UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
                END
            """)

        conn.commit()
        print("\n[OK] 记忆数据库初始化完成!")

    except Exception as e:
        print(f"[ERROR] 记忆数据库初始化失败: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_memory_tables()
