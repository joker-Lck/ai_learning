"""
向量化服务模块 - 使用讯飞星火 Embedding API
支持文本向量化和相似度计算
"""

from openai import OpenAI
import numpy as np
import requests
import json
import base64
import hmac
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse
from dotenv import load_dotenv
import os
from core.logger import info, error, warning

load_dotenv()

class EmbeddingService:
    """向量化服务类（懒加载：首次调用时才初始化客户端）"""

    def __init__(self):
        self._client = None
        self._embedding_url = None
        self._api_key = None
        self._api_secret = None
        self._app_id = None

    def _init_config(self):
        """初始化配置"""
        if self._embedding_url is None:
            self._embedding_url = os.getenv('SPARK_EMBEDDING_URL', 'http://emb-cn-huabei-1.xf-yun.com/')
            self._api_key = os.getenv('SPARK_IMAGE_API_KEY', os.getenv('SPARK_API_KEY', ''))
            self._api_secret = os.getenv('SPARK_IMAGE_API_SECRET', os.getenv('SPARK_API_SECRET', ''))
            self._app_id = os.getenv('SPARK_IMAGE_APPID', os.getenv('SPARK_APPID', ''))

    def _format_date(self, dt):
        """格式化日期为RFC1123"""
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        return f'{days[dt.weekday()]}, {dt.day:02d} {months[dt.month-1]} {dt.year} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} GMT'

    def _create_auth_url(self, base_url):
        """生成讯飞鉴权URL"""
        parsed = urlparse(base_url)
        host = parsed.hostname
        path = parsed.path or '/'

        now = datetime.now(timezone.utc)
        date = self._format_date(now)

        signature_origin = f'host: {host}\ndate: {date}\nPOST {path} HTTP/1.1'
        signature_sha = hmac.new(
            self._api_secret.encode('utf-8'),
            signature_origin.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature = base64.b64encode(signature_sha).decode('utf-8')

        authorization_origin = f'api_key="{self._api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')

        v = {
            'authorization': authorization,
            'date': date,
            'host': host,
        }
        return f'{base_url}?{urlencode(v)}'

    def get_embedding(self, text, model='general'):
        """
        获取文本的向量表示

        参数：
        - text: 要向量化的文本
        - model: 使用的模型（保留兼容性）

        返回：
        - list: 2560维向量数组
        """
        try:
            self._init_config()

            text = text[:8000]

            if not text.strip():
                return [0.0] * 2560

            # 使用讯飞Embedding HTTP API
            url = self._create_auth_url(self._embedding_url)

            text_json = json.dumps({'messages': [{'content': text, 'role': 'user'}]})
            text_base64 = base64.b64encode(text_json.encode('utf-8')).decode('utf-8')

            body = {
                'header': {
                    'app_id': self._app_id,
                    'uid': 'embedding_user',
                    'status': 3
                },
                'parameter': {
                    'emb': {
                        'domain': 'query',
                        'feature': {
                            'encoding': 'utf8',
                            'compress': 'raw',
                            'format': 'plain'
                        }
                    }
                },
                'payload': {
                    'messages': {
                        'encoding': 'utf8',
                        'compress': 'raw',
                        'format': 'json',
                        'status': 3,
                        'text': text_base64
                    }
                }
            }

            resp = requests.post(url, json=body, timeout=30)
            result = resp.json()

            code = result.get('header', {}).get('code', -1)
            if code == 0:
                text_b64 = result['payload']['feature']['text']
                text_data = base64.b64decode(text_b64)
                dt = np.dtype(np.float32).newbyteorder('<')
                vector = np.frombuffer(text_data, dtype=dt)
                return vector.tolist()
            else:
                msg = result.get('header', {}).get('message', 'unknown error')
                error(f"Embedding API error: {msg}")
                return None

        except Exception as e:
            error(f"获取向量失败：{str(e)}")
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
            error(f"计算相似度失败：{str(e)}")
            return 0.0


# 创建全局向量化服务实例
embedding_service = EmbeddingService()
