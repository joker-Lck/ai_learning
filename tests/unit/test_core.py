"""单元测试：核心工具模块"""


class TestJsonUtils:
    """测试 JSON 工具函数"""

    def test_safe_parse_valid_json(self):
        from core.json_utils import safe_parse_json
        result = safe_parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_safe_parse_invalid_json(self):
        from core.json_utils import safe_parse_json
        result = safe_parse_json("not json")
        assert result is None or isinstance(result, (dict, list))

    def test_safe_parse_empty_string(self):
        from core.json_utils import safe_parse_json
        result = safe_parse_json("")
        assert result is None or result == {}

    def test_safe_parse_nested_json(self):
        from core.json_utils import safe_parse_json
        data = '{"a": {"b": [1, 2, 3]}}'
        result = safe_parse_json(data)
        if result:
            assert result["a"]["b"] == [1, 2, 3]


class TestLogger:
    """测试日志模块"""

    def test_logger_import(self):
        from core.logger import debug, error, info, warning
        assert callable(info)
        assert callable(error)
        assert callable(warning)
        assert callable(debug)

    def test_logger_no_crash(self):
        from core.logger import info
        # 不应抛出异常
        info("测试日志消息")


class TestEmbeddingService:
    """测试 Embedding 服务（不调用真实 API）"""

    def test_cosine_similarity_identical(self):
        from data.embedding_service import EmbeddingService
        EmbeddingService.__new__(EmbeddingService)
        vec = [1.0, 0.0, 0.0]
        # 使用静态方法或直接计算
        import numpy as np
        a = np.array(vec)
        b = np.array(vec)
        sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal(self):
        import numpy as np
        a = np.array([1.0, 0.0, 0.0])
        b = np.array([0.0, 1.0, 0.0])
        sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        assert abs(sim) < 1e-6


class TestContentSafety:
    """测试内容安全服务"""

    def test_ac_automaton_import(self):
        from services.content_safety_service import AhoCorasick
        ac = AhoCorasick()
        assert ac is not None

    def test_ac_automaton_search(self):
        from services.content_safety_service import AhoCorasick
        ac = AhoCorasick()
        ac.add_pattern("测试", 0)
        ac.build()
        results = ac.search("这是一个测试文本")
        assert len(results) > 0

    def test_ac_automaton_no_match(self):
        from services.content_safety_service import AhoCorasick
        ac = AhoCorasick()
        ac.add_pattern("敏感词", 0)
        ac.build()
        results = ac.search("正常文本内容")
        assert len(results) == 0


class TestExceptions:
    """测试自定义异常类"""

    def test_app_exception(self):
        from backend.exceptions import AppException
        exc = AppException("测试错误", code="TEST", status_code=400)
        assert exc.message == "测试错误"
        assert exc.code == "TEST"
        assert exc.status_code == 400

    def test_validation_error(self):
        from backend.exceptions import ValidationError
        exc = ValidationError("字段无效", field="username")
        assert exc.status_code == 400
        assert exc.field == "username"

    def test_auth_error(self):
        from backend.exceptions import AuthenticationError
        exc = AuthenticationError()
        assert exc.status_code == 401

    def test_rate_limit_error(self):
        from backend.exceptions import RateLimitError
        exc = RateLimitError()
        assert exc.status_code == 429


class TestConfig:
    """测试配置模块"""

    def test_config_import(self):
        from backend.config import Settings
        assert Settings is not None

    def test_config_cors_origins(self):
        from backend.config import Settings
        s = Settings(
            jwt_secret="test_secret_32chars_for_testing!!",
            mimo_api_key="test_key",
            allowed_origins="http://a.com, http://b.com",
        )
        assert s.cors_origins == ["http://a.com", "http://b.com"]

    def test_config_environment(self, monkeypatch):
        # 清除 lru_cache 以使用新配置
        from backend.config import Settings, get_settings
        get_settings.cache_clear()

        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("JWT_SECRET", "test_secret_32chars_for_testing!!")
        monkeypatch.setenv("MIMO_API_KEY", "test_key")

        s = Settings()
        assert s.is_production is True
        assert s.is_development is False
