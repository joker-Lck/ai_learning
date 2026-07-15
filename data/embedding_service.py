"""
向量化服务模块 - 使用 MiMo Embedding API
支持文本向量化和相似度计算
"""

import os

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

from core.logger import error, info

load_dotenv(override=True)

class EmbeddingService:
    """向量化服务类（懒加载：首次调用时才初始化客户端）"""

    def __init__(self):
        self._client = None
        self._embedding_model = None

    def _init_client(self):
        """初始化 MiMo Embedding 客户端"""
        if self._client is None:
            api_key = os.getenv('MIMO_API_KEY', '')
            base_url = os.getenv('MIMO_BASE_URL', 'https://api.xiaomimimo.com/v1')

            if not api_key:
                raise RuntimeError("MIMO_API_KEY 未配置")

            self._client = OpenAI(
                api_key=api_key,
                base_url=base_url,
            )
            self._embedding_model = os.getenv('MIMO_EMBEDDING_MODEL', 'mimo-embedding')
            info(f"MiMo Embedding 客户端初始化完成 (model={self._embedding_model})")

    def get_embedding(self, text, model=None):
        """
        获取文本的向量表示

        参数：
        - text: 要向量化的文本
        - model: 使用的模型（可选，默认使用 mimo-embedding）

        返回：
        - list: 向量数组（维度由模型决定）
        """
        try:
            self._init_client()

            text = text[:8000]

            if not text.strip():
                return [0.0] * 768

            embed_model = model or self._embedding_model

            response = self._client.embeddings.create(
                model=embed_model,
                input=text,
            )

            vector = response.data[0].embedding
            return vector

        except Exception as e:
            error(f"获取向量失败：{e!s}")
            return None

    def cosine_similarity(self, vec1, vec2):
        """
        计算两个向量的余弦相似度
        """
        try:
            if vec1 is None or vec2 is None:
                return 0.0

            vec1 = np.array(vec1)
            vec2 = np.array(vec2)

            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

            return float(similarity)

        except Exception as e:
            error(f"计算相似度失败：{e!s}")
            return 0.0


# 创建全局向量化服务实例
embedding_service = EmbeddingService()
