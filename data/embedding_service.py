"""
向量化服务模块 - 使用讯飞星火 Embedding API
支持文本向量化和相似度计算
"""

from openai import OpenAI
import numpy as np
from dotenv import load_dotenv
import os
from core.logger import info, error, warning

load_dotenv()

class EmbeddingService:
    """向量化服务类（懒加载：首次调用时才初始化客户端）"""

    def __init__(self):
        """初始化 — 延迟到首次使用时"""
        self._client = None

    @property
    def client(self):
        if self._client is None:
            api_key = os.getenv('SPARK_API_KEY', '')
            api_secret = os.getenv('SPARK_API_SECRET', '')
            base_url = os.getenv('SPARK_BASE_URL', 'https://spark-api-open.xf-yun.com/v1')
            if not api_key:
                raise RuntimeError(
                    "SPARK_API_KEY 未配置，请在 .env 文件中设置。"
                    "参考 .env.example"
                )
            # 讯飞星火 OpenAI 兼容接口
            if api_secret:
                from services.spark_client import _generate_spark_token
                token = _generate_spark_token(api_key, api_secret)
            else:
                token = api_key
            self._client = OpenAI(api_key=token, base_url=base_url)
        return self._client
    
    def get_embedding(self, text, model='general'):
        """
        获取文本的向量表示
        
        参数：
        - text: 要向量化的文本
        - model: 使用的模型
        
        返回：
        - list: 向量数组
        """
        try:
            # 限制文本长度，避免超出模型限制
            text = text[:8000]
            
            if not text.strip():
                return [0.0] * 768  # 返回零向量
            
            response = self.client.embeddings.create(
                model=model,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            error(f"获取向量失败：{str(e)}")
            return None
    
    def cosine_similarity(self, vec1, vec2):
        """
        计算两个向量的余弦相似度
        
        参数：
        - vec1: 第一个向量
        - vec2: 第二个向量
        
        返回：
        - float: 相似度值（0-1）
        """
        try:
            if vec1 is None or vec2 is None:
                return 0.0
            
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            # 计算余弦相似度
            similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
            
            return float(similarity)
            
        except Exception as e:
            error(f"计算相似度失败：{str(e)}")
            return 0.0


# 创建全局向量化服务实例
embedding_service = EmbeddingService()
