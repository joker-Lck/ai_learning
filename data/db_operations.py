"""
MySQL 数据库操作模块（JSON 格式存储）
提供数据库 CRUD 操作，所有复杂数据以 JSON 格式存储
"""

from data import dbapi as dbapi

from core.logger import db_operation_failed, debug, error

from .config import (
    get_agents_db_config,
    get_assessments_db_config,
    get_db_config,
    get_paths_db_config,
    get_profile_db_config,
    get_resources_db_config,
)


class Database:
    def __init__(self, config_func=None):
        self.conn = None
        self.cursor = None
        self._config_func = config_func or get_db_config

    def connect(self):
        """连接数据库"""
        try:
            config = self._config_func()
            db_path = config["database"]
            self.conn = dbapi.connect(db_path, timeout=10)
            self.conn.row_factory = dbapi.Row
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA foreign_keys=ON")
            self.cursor = self.conn.cursor()
            debug(f"MySQL 连接成功: {db_path}")
            return True
        except Exception as e:
            error(f"数据库连接失败：{e!s}")
            db_operation_failed("connect", str(e))
            return False

    def close(self):
        """关闭连接"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
        except Exception as e:
            error(f"关闭连接失败：{e!s}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# 创建全局数据库实例
db = Database()  # 默认使用 auth 数据库

# 创建特定功能的数据库实例
profile_db = Database(config_func=get_profile_db_config)
resource_db = Database(config_func=get_resources_db_config)
path_db = Database(config_func=get_paths_db_config)
assessment_db = Database(config_func=get_assessments_db_config)
agent_db = Database(config_func=get_agents_db_config)
