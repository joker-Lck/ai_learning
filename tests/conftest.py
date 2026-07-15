"""Pytest 全局 fixtures"""
import os
import sys
import sqlite3
import tempfile
import pytest

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def tmp_db(tmp_path):
    """创建临时 SQLite 数据库"""
    db_path = str(tmp_path / "test.db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    yield db_path
    conn.close()


@pytest.fixture
def mock_env(monkeypatch):
    """设置测试环境变量"""
    monkeypatch.setenv("JWT_SECRET", "test_secret_key_for_testing_only_32chars!")
    monkeypatch.setenv("MIMO_API_KEY", "test_api_key")
    monkeypatch.setenv("MIMO_BASE_URL", "https://api.mimo.ai/v1")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


@pytest.fixture
def sample_user():
    """测试用户数据"""
    return {
        "id": 1,
        "username": "testuser",
        "role": "student",
    }


@pytest.fixture
def sample_profile():
    """测试画像数据"""
    return {
        "knowledge_base": "计算机科学基础",
        "cognitive_style": "visual",
        "learning_goals": "掌握机器学习",
        "skill_level": "intermediate",
        "learning_preferences": ["视频", "代码实践"],
        "strengths": ["数学基础", "编程能力"],
        "weaknesses": ["理论推导"],
        "motivation": "内在兴趣",
        "major_and_grade": "计算机科学 大三",
    }


@pytest.fixture
def sample_resource():
    """测试资源数据"""
    return {
        "title": "二叉树遍历详解",
        "resource_type": "document",
        "subject": "数据结构",
        "topic": "二叉树",
        "difficulty_level": "intermediate",
        "content_data": {
            "summary": "二叉树的前序、中序、后序遍历",
            "sections": ["前序遍历", "中序遍历", "后序遍历"],
        },
    }
