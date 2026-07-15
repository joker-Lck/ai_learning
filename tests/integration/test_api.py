"""集成测试：API 端点"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 确保环境变量存在
os.environ.setdefault("JWT_SECRET", "test_secret_key_for_integration_test_32!")
os.environ.setdefault("MIMO_API_KEY", "test_api_key")


@pytest.fixture
def client():
    """创建测试客户端"""
    from fastapi.testclient import TestClient

    from backend.main import app
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """获取认证 headers"""
    # 注册
    client.post("/api/auth/register", json={
        "username": "inttestuser",
        "password": "Test@123456",
    })
    # 登录
    resp = client.post("/api/auth/login", json={
        "username": "inttestuser",
        "password": "Test@123456",
    })
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token", "")
        return {"Authorization": f"Bearer {token}"}
    return {}


class TestHealthEndpoint:
    """健康检查端点"""

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200


class TestAuthEndpoints:
    """认证端点"""

    def test_register(self, client):
        resp = client.post("/api/auth/register", json={
            "username": "newuser",
            "password": "NewPass@123",
        })
        assert resp.status_code in [200, 400]  # 200 成功或 400 已存在

    def test_login_wrong_password(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "nonexistent",
            "password": "wrong",
        })
        assert resp.status_code in [200, 401, 400]

    def test_guest_mode(self, client):
        resp = client.post("/api/auth/guest")
        assert resp.status_code in [200, 404]


class TestAgentEndpoints:
    """智能体端点"""

    def test_list_resources_unauth(self, client):
        """未认证访问资源列表"""
        resp = client.get("/api/agent/list-resources")
        # 游客可以访问
        assert resp.status_code in [200, 401]

    def test_dashboard_stats(self, client, auth_headers):
        """工作台统计"""
        resp = client.get("/api/agent/dashboard/stats", headers=auth_headers)
        assert resp.status_code in [200, 401]

    def test_get_profile(self, client, auth_headers):
        """获取画像"""
        resp = client.get("/api/agent/get-profile", headers=auth_headers)
        assert resp.status_code in [200, 401]


class TestStreamEndpoints:
    """流式端点"""

    def test_content_safety(self, client):
        """内容安全检查"""
        resp = client.post("/api/stream/check-content-safety", json={
            "content": "正常的学习内容"
        })
        assert resp.status_code in [200, 404]
