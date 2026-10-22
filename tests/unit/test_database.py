"""单元测试：数据库操作（MySQL）"""
import os

from data import dbapi as sqlite3


class TestDatabaseInit:
    """测试数据库初始化"""

    def test_init_script_importable(self):
        """初始化脚本可以导入"""
        import importlib.util

        spec = importlib.util.spec_from_file_location("init_databases", "scripts/init_databases.py")
        assert spec is not None

    def test_all_db_names_defined(self):
        """所有数据库名已定义"""
        from data.config import (
            get_agents_db_path,
            get_assessments_db_path,
            get_auth_db_path,
            get_memory_db_path,
            get_paths_db_path,
            get_profile_db_path,
            get_rag_db_path,
            get_resources_db_path,
            get_tutor_db_path,
        )

        names = [
            get_auth_db_path(), get_profile_db_path(), get_resources_db_path(),
            get_paths_db_path(), get_tutor_db_path(), get_assessments_db_path(),
            get_agents_db_path(), get_rag_db_path(), get_memory_db_path(),
        ]
        assert len(names) == 9
        assert all(isinstance(n, str) and n.startswith("ai_") for n in names)

    def test_db_name_format(self):
        """数据库名格式正确"""
        from data.config import get_auth_db_path

        assert get_auth_db_path() == "ai_auth"


class TestDAO:
    """测试 DAO 层"""

    def test_resource_dao_import(self):
        from data.dao import ResourceDAO

        assert ResourceDAO is not None

    def test_activity_dao_import(self):
        from data.dao import ActivityDAO

        assert ActivityDAO is not None

    def test_dao_singletons(self):
        from data.dao import get_resource_dao

        dao1 = get_resource_dao()
        dao2 = get_resource_dao()
        assert dao1 is dao2  # 单例

    def test_db_operations_import(self):
        from data.db_operations import Database

        assert Database is not None

    def test_db_context_manager(self):
        """Database 上下文管理器"""
        from data.db_operations import Database

        db = Database()
        assert db.connect() is True
        db.close()


class TestMemoryDB:
    """测试记忆数据库表结构"""

    def _tables(self, schema: str) -> list[str]:
        conn = sqlite3.connect(schema)
        try:
            cursor = conn.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema=%s AND table_type='BASE TABLE'",
                (schema,),
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def test_memory_tables_exist(self):
        """记忆系统表存在"""
        tables = self._tables("ai_memory")
        expected = [
            "short_term_memory", "episodic_memory", "semantic_memory",
            "entity_memory", "entity_relations", "memory_metadata",
        ]
        for t in expected:
            assert t in tables, f"缺少表: {t}"

    def test_feedback_tables_exist(self):
        """反馈表存在"""
        tables = self._tables("ai_memory")
        assert "user_feedback" in tables, "缺少 user_feedback 表"
        assert "learning_experiences" in tables, "缺少 learning_experiences 表"
