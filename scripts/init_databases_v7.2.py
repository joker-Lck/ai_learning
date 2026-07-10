"""
SQLite 多数据库架构初始化脚本
9个独立 .db 文件，与原 MySQL 架构一一对应
"""

import sqlite3
from data.config import (
    get_auth_db_path,
    get_profile_db_path,
    get_resources_db_path,
    get_paths_db_path,
    get_tutor_db_path,
    get_assessments_db_path,
    get_agents_db_path,
    get_rag_db_path,
    get_memory_db_path
)


def _connect(db_path: str) -> sqlite3.Connection:
    """连接 SQLite 数据库并启用必要 PRAGMA"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _add_updated_at_trigger(conn, table: str):
    """为表添加 updated_at 自动更新触发器"""
    conn.execute(f"""
        CREATE TRIGGER IF NOT EXISTS trg_{table}_updated_at
        AFTER UPDATE ON {table}
        FOR EACH ROW
        BEGIN
            UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
        END
    """)


def init_auth_database():
    """初始化认证数据库"""
    conn = _connect(get_auth_db_path())
    try:
        print("\n[INIT] 初始化认证数据库 (ai_auth)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT CHECK(role IN ('user', 'admin', 'guest')) DEFAULT 'user',
                major TEXT,
                grade_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
            CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
        """)
        _add_updated_at_trigger(conn, 'users')
        conn.commit()
        print("  [OK] 认证数据库初始化完成!")
    finally:
        conn.close()


def init_profile_database():
    """初始化学生画像数据库"""
    conn = _connect(get_profile_db_path())
    try:
        print("\n[INIT] 初始化学生画像数据库 (ai_profiles)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                profile_data TEXT NOT NULL,
                conversation_log TEXT,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_profiles_user ON student_profiles(user_id);

            CREATE TABLE IF NOT EXISTS course_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                courses TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, semester)
            );

            CREATE TABLE IF NOT EXISTS student_grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                course_name TEXT NOT NULL,
                score REAL,
                credits REAL,
                grade_type TEXT DEFAULT 'exam',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_grades_user_sem ON student_grades(user_id, semester);

            CREATE TABLE IF NOT EXISTS error_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                chapter TEXT,
                question TEXT NOT NULL,
                my_answer TEXT,
                correct_answer TEXT,
                error_reason TEXT,
                tags TEXT,
                mastery INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_error_user ON error_notes(user_id);
            CREATE INDEX IF NOT EXISTS idx_error_subject ON error_notes(user_id, subject);
            CREATE INDEX IF NOT EXISTS idx_error_mastery ON error_notes(user_id, mastery);

            CREATE TABLE IF NOT EXISTS study_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                plan_type TEXT DEFAULT 'weekly',
                plan_data TEXT NOT NULL,
                status TEXT CHECK(status IN ('active', 'completed', 'expired')) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_plans_user_sem ON study_plans(user_id, semester);
            CREATE INDEX IF NOT EXISTS idx_plans_status ON study_plans(user_id, status);
        """)
        _add_updated_at_trigger(conn, 'student_profiles')
        _add_updated_at_trigger(conn, 'course_schedules')
        _add_updated_at_trigger(conn, 'study_plans')
        conn.commit()
        print("  [OK] 学生画像数据库初始化完成!")
    finally:
        conn.close()


def init_resources_database():
    """初始化学习资源数据库"""
    conn = _connect(get_resources_db_path())
    try:
        print("\n[INIT] 初始化学习资源数据库 (ai_resources)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS learning_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                resource_type TEXT CHECK(resource_type IN ('document', 'mindmap', 'quiz', 'video', 'animation', 'code_case', 'reading')) NOT NULL,
                subject TEXT,
                topic TEXT,
                difficulty_level TEXT CHECK(difficulty_level IN ('beginner', 'intermediate', 'advanced')) DEFAULT 'intermediate',
                content_data TEXT NOT NULL,
                file_path TEXT,
                thumbnail_path TEXT,
                generated_by_agent TEXT,
                target_profile TEXT,
                tags TEXT,
                usage_count INTEGER DEFAULT 0,
                rating REAL DEFAULT 0,
                duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_resources_user ON learning_resources(user_id);
            CREATE INDEX IF NOT EXISTS idx_resources_type_subject ON learning_resources(resource_type, subject);
            CREATE INDEX IF NOT EXISTS idx_resources_difficulty ON learning_resources(difficulty_level);

            CREATE TABLE IF NOT EXISTS resource_safety_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER,
                safety_check_result TEXT NOT NULL,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES learning_resources(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_safety_resource ON resource_safety_logs(resource_id);
        """)
        _add_updated_at_trigger(conn, 'learning_resources')
        conn.commit()
        print("  [OK] 学习资源数据库初始化完成!")
    finally:
        conn.close()


def init_paths_database():
    """初始化学习路径数据库"""
    conn = _connect(get_paths_db_path())
    try:
        print("\n[INIT] 初始化学习路径数据库 (ai_paths)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                path_name TEXT NOT NULL,
                description TEXT,
                path_data TEXT NOT NULL,
                current_step INTEGER DEFAULT 1,
                status TEXT CHECK(status IN ('active', 'completed', 'paused', 'archived')) DEFAULT 'active',
                total_steps INTEGER DEFAULT 0,
                completed_steps INTEGER DEFAULT 0,
                estimated_hours REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_paths_user_status ON learning_paths(user_id, status);

            CREATE TABLE IF NOT EXISTS path_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                step_number INTEGER NOT NULL,
                completed_at TIMESTAMP,
                time_spent INTEGER,
                FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_progress_path ON path_progress(path_id);
            CREATE INDEX IF NOT EXISTS idx_progress_user ON path_progress(user_id);
        """)
        _add_updated_at_trigger(conn, 'learning_paths')
        conn.commit()
        print("  [OK] 学习路径数据库初始化完成!")
    finally:
        conn.close()


def init_tutor_database():
    """初始化智能辅导数据库"""
    conn = _connect(get_tutor_db_path())
    try:
        print("\n[INIT] 初始化智能辅导数据库 (ai_tutor)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tutor_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT,
                session_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tutor_sessions_user ON tutor_sessions(user_id);

            CREATE TABLE IF NOT EXISTS tutor_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
                content TEXT NOT NULL,
                diagram TEXT,
                example TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES tutor_sessions(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_tutor_msgs_session ON tutor_messages(session_id);

            CREATE TABLE IF NOT EXISTS tutor_knowledge_refs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                rag_source TEXT,
                confidence_score REAL,
                FOREIGN KEY (message_id) REFERENCES tutor_messages(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_knowledge_refs_msg ON tutor_knowledge_refs(message_id);
        """)
        _add_updated_at_trigger(conn, 'tutor_sessions')
        conn.commit()
        print("  [OK] 智能辅导数据库初始化完成!")
    finally:
        conn.close()


def init_assessments_database():
    """初始化学习评估数据库"""
    conn = _connect(get_assessments_db_path())
    try:
        print("\n[INIT] 初始化学习评估数据库 (ai_assessments)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS learning_assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                assessment_type TEXT CHECK(assessment_type IN ('weekly', 'monthly', 'custom', 'comprehensive', 'auto_generated')) NOT NULL,
                assessment_data TEXT NOT NULL,
                period_start TEXT,
                period_end TEXT,
                overall_score REAL,
                improvement_suggestions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_assessments_user ON learning_assessments(user_id);
            CREATE INDEX IF NOT EXISTS idx_assessments_type ON learning_assessments(assessment_type);

            CREATE TABLE IF NOT EXISTS assessment_dimensions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                assessment_id INTEGER NOT NULL,
                dimension_name TEXT NOT NULL,
                score REAL NOT NULL,
                max_score REAL NOT NULL,
                level TEXT,
                feedback TEXT,
                FOREIGN KEY (assessment_id) REFERENCES learning_assessments(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_dimensions_assessment ON assessment_dimensions(assessment_id);

            CREATE TABLE IF NOT EXISTS learning_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                metadata TEXT,
                duration_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_activities_user ON learning_activities(user_id);
            CREATE INDEX IF NOT EXISTS idx_activities_type ON learning_activities(activity_type);
        """)
        conn.commit()
        print("  [OK] 学习评估数据库初始化完成!")
    finally:
        conn.close()


def init_agents_database():
    """初始化智能体协作数据库"""
    conn = _connect(get_agents_db_path())
    try:
        print("\n[INIT] 初始化智能体协作数据库 (ai_agents)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS agent_collaboration_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER,
                task_type TEXT NOT NULL,
                coordinator_input TEXT,
                agent_outputs TEXT,
                final_result TEXT,
                execution_time_ms INTEGER,
                status TEXT CHECK(status IN ('success', 'failed', 'timeout')) DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_collab_session ON agent_collaboration_logs(session_id);
            CREATE INDEX IF NOT EXISTS idx_collab_user_task ON agent_collaboration_logs(user_id, task_type);

            CREATE TABLE IF NOT EXISTS agent_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_type TEXT NOT NULL,
                assigned_agent TEXT,
                input_data TEXT,
                output_data TEXT,
                status TEXT CHECK(status IN ('pending', 'running', 'completed', 'failed')) DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_status ON agent_tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_agent ON agent_tasks(assigned_agent);
        """)
        conn.commit()
        print("  [OK] 智能体协作数据库初始化完成!")
    finally:
        conn.close()


def init_rag_database():
    """初始化RAG知识库数据库"""
    conn = _connect(get_rag_db_path())
    try:
        print("\n[INIT] 初始化RAG知识库数据库 (ai_rag_knowledge)...")
        conn.executescript("""
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
            );
            CREATE INDEX IF NOT EXISTS idx_kd_subject ON knowledge_documents(subject);
            CREATE INDEX IF NOT EXISTS idx_kd_upload_time ON knowledge_documents(upload_time);
            CREATE INDEX IF NOT EXISTS idx_kd_uploaded_by ON knowledge_documents(uploaded_by);
            CREATE INDEX IF NOT EXISTS idx_kd_usage_count ON knowledge_documents(usage_count);

            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_documents_fts USING fts5(
                title, subject,
                content='knowledge_documents', content_rowid='id',
                tokenize='unicode61'
            );

            CREATE TRIGGER IF NOT EXISTS kd_fts_insert AFTER INSERT ON knowledge_documents BEGIN
                INSERT INTO knowledge_documents_fts(rowid, title, subject)
                VALUES (new.id, new.title, new.subject);
            END;

            CREATE TRIGGER IF NOT EXISTS kd_fts_delete AFTER DELETE ON knowledge_documents BEGIN
                INSERT INTO knowledge_documents_fts(knowledge_documents_fts, rowid, title, subject)
                VALUES ('delete', old.id, old.title, old.subject);
            END;

            CREATE TRIGGER IF NOT EXISTS kd_fts_update AFTER UPDATE ON knowledge_documents BEGIN
                INSERT INTO knowledge_documents_fts(knowledge_documents_fts, rowid, title, subject)
                VALUES ('delete', old.id, old.title, old.subject);
                INSERT INTO knowledge_documents_fts(rowid, title, subject)
                VALUES (new.id, new.title, new.subject);
            END;

            CREATE TABLE IF NOT EXISTS knowledge_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                point_name TEXT NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                UNIQUE(doc_id, point_name)
            );
            CREATE INDEX IF NOT EXISTS idx_kp_point_name ON knowledge_points(point_name);

            CREATE TABLE IF NOT EXISTS document_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT NOT NULL,
                parent_id INTEGER,
                subject TEXT,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (parent_id) REFERENCES document_categories(id) ON DELETE SET NULL,
                UNIQUE(category_name)
            );
            CREATE INDEX IF NOT EXISTS idx_cat_parent ON document_categories(parent_id);
            CREATE INDEX IF NOT EXISTS idx_cat_subject ON document_categories(subject);

            CREATE TABLE IF NOT EXISTS document_category_relation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE CASCADE,
                UNIQUE(doc_id, category_id)
            );

            CREATE TABLE IF NOT EXISTS document_usage_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                user_id INTEGER,
                action_type TEXT,
                action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                search_keywords TEXT,
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_usage_doc ON document_usage_log(doc_id);
            CREATE INDEX IF NOT EXISTS idx_usage_user ON document_usage_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_usage_time ON document_usage_log(action_time);
        """)

        # 基础学科分类种子数据
        conn.executemany("""
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

        conn.commit()
        print("  [OK] RAG知识库数据库初始化完成!")
    finally:
        conn.close()


def init_memory_database():
    """初始化记忆系统数据库"""
    conn = _connect(get_memory_db_path())
    try:
        print("\n[INIT] 初始化记忆系统数据库 (ai_memory)...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                role TEXT CHECK(role IN ('user', 'assistant', 'system')) NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER DEFAULT 0,
                position INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_stm_user_session ON short_term_memory(user_id, session_id);
            CREATE INDEX IF NOT EXISTS idx_stm_created ON short_term_memory(created_at);

            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                episode_type TEXT CHECK(episode_type IN ('conversation', 'task', 'event', 'learning')) NOT NULL,
                title TEXT NOT NULL,
                summary TEXT,
                context TEXT,
                emotions TEXT,
                participants TEXT,
                location TEXT,
                importance REAL DEFAULT 0.5,
                embedding BLOB,
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_em_user ON episodic_memory(user_id);
            CREATE INDEX IF NOT EXISTS idx_em_type ON episodic_memory(episode_type);
            CREATE INDEX IF NOT EXISTS idx_em_importance ON episodic_memory(importance);

            CREATE VIRTUAL TABLE IF NOT EXISTS episodic_memory_fts USING fts5(
                title, summary, content,
                content='episodic_memory', content_rowid='id',
                tokenize='unicode61'
            );

            CREATE TRIGGER IF NOT EXISTS em_fts_insert AFTER INSERT ON episodic_memory BEGIN
                INSERT INTO episodic_memory_fts(rowid, title, summary, content)
                VALUES (new.id, new.title, new.summary, new.context);
            END;

            CREATE TRIGGER IF NOT EXISTS em_fts_delete AFTER DELETE ON episodic_memory BEGIN
                INSERT INTO episodic_memory_fts(episodic_memory_fts, rowid, title, summary, content)
                VALUES ('delete', old.id, old.title, old.summary, old.context);
            END;

            CREATE TRIGGER IF NOT EXISTS em_fts_update AFTER UPDATE ON episodic_memory BEGIN
                INSERT INTO episodic_memory_fts(episodic_memory_fts, rowid, title, summary, content)
                VALUES ('delete', old.id, old.title, old.summary, old.context);
                INSERT INTO episodic_memory_fts(rowid, title, summary, content)
                VALUES (new.id, new.title, new.summary, new.context);
            END;

            CREATE TABLE IF NOT EXISTS semantic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                fact_type TEXT CHECK(fact_type IN ('preference', 'knowledge', 'belief', 'habit', 'skill')) NOT NULL,
                subject TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                source TEXT DEFAULT '',
                embedding BLOB,
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, subject, predicate, object)
            );
            CREATE INDEX IF NOT EXISTS idx_sm_user ON semantic_memory(user_id);
            CREATE INDEX IF NOT EXISTS idx_sm_type ON semantic_memory(fact_type);
            CREATE INDEX IF NOT EXISTS idx_sm_subject ON semantic_memory(subject);

            CREATE TABLE IF NOT EXISTS entity_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                entity_type TEXT CHECK(entity_type IN ('person', 'place', 'concept', 'object', 'event')) NOT NULL,
                entity_name TEXT NOT NULL,
                entity_alias TEXT,
                attributes TEXT,
                description TEXT,
                importance REAL DEFAULT 0.5,
                embedding BLOB,
                access_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, entity_type, entity_name)
            );
            CREATE INDEX IF NOT EXISTS idx_entity_user ON entity_memory(user_id);
            CREATE INDEX IF NOT EXISTS idx_entity_type ON entity_memory(entity_type);
            CREATE INDEX IF NOT EXISTS idx_entity_name ON entity_memory(entity_name);

            CREATE TABLE IF NOT EXISTS entity_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                source_entity_id INTEGER NOT NULL,
                target_entity_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE,
                FOREIGN KEY (target_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE,
                UNIQUE(user_id, source_entity_id, target_entity_id, relation_type)
            );
            CREATE INDEX IF NOT EXISTS idx_rel_source ON entity_relations(source_entity_id);
            CREATE INDEX IF NOT EXISTS idx_rel_target ON entity_relations(target_entity_id);

            CREATE TABLE IF NOT EXISTS memory_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT CHECK(memory_type IN ('episodic', 'semantic', 'entity')) NOT NULL,
                memory_id INTEGER NOT NULL,
                importance REAL DEFAULT 0.5,
                decay_rate REAL DEFAULT 0.01,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                is_forgotten INTEGER DEFAULT 0,
                forgotten_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_type, memory_id)
            );
            CREATE INDEX IF NOT EXISTS idx_meta_type ON memory_metadata(memory_type);
            CREATE INDEX IF NOT EXISTS idx_meta_forgotten ON memory_metadata(is_forgotten);

            CREATE TABLE IF NOT EXISTS memory_conflicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                conflict_type TEXT CHECK(conflict_type IN ('contradiction', 'update', 'merge')) NOT NULL,
                old_memory_type TEXT,
                old_memory_id INTEGER,
                new_memory_type TEXT,
                new_memory_id INTEGER,
                resolution TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_conflict_user ON memory_conflicts(user_id);
            CREATE INDEX IF NOT EXISTS idx_conflict_resolved ON memory_conflicts(resolved);

            CREATE TABLE IF NOT EXISTS memory_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                memory_type TEXT NOT NULL,
                memory_id INTEGER NOT NULL,
                access_type TEXT CHECK(access_type IN ('read', 'write', 'delete', 'search')) NOT NULL,
                access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_access_user ON memory_access_log(user_id);
            CREATE INDEX IF NOT EXISTS idx_access_time ON memory_access_log(access_time);
        """)

        # 为需要 updated_at 的表添加触发器
        for table in ['episodic_memory', 'semantic_memory', 'entity_memory', 'entity_relations']:
            _add_updated_at_trigger(conn, table)

        conn.commit()
        print("  [OK] 记忆系统数据库初始化完成!")
    finally:
        conn.close()


def main():
    """主函数: 初始化所有数据库"""
    print("=" * 60)
    print("SQLite 多数据库架构初始化脚本")
    print("=" * 60)

    init_auth_database()
    init_profile_database()
    init_resources_database()
    init_paths_database()
    init_tutor_database()
    init_assessments_database()
    init_agents_database()
    init_rag_database()
    init_memory_database()

    print("\n" + "=" * 60)
    print("所有数据库初始化完成!")
    print("=" * 60)
    print("\n数据库列表:")
    print("  1. ai_auth.db - 认证与用户管理")
    print("  2. ai_profiles.db - 学生画像")
    print("  3. ai_resources.db - 学习资源")
    print("  4. ai_paths.db - 学习路径")
    print("  5. ai_tutor.db - 智能辅导")
    print("  6. ai_assessments.db - 学习效果评估")
    print("  7. ai_agents.db - 智能体协作")
    print("  8. ai_rag_knowledge.db - RAG知识库")
    print("  9. ai_memory.db - 记忆系统")


if __name__ == "__main__":
    main()
