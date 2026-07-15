"""
向量化服务模块 - TF-IDF + SVD 降维
适合长文本语义检索，纯本地实现无需网络
"""

import hashlib
import os
import threading

import jieba
import numpy as np
from dotenv import load_dotenv

from core.logger import error, info

load_dotenv(override=True)

# 停用词
STOP_WORDS = frozenset({
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '自己', '这', '他', '她', '它', '们', '那', '些', '么', '等', '而', '吗', '呢',
    '把', '被', '比', '如', '从', '对', '但', '以', '与', '又', '或', '之', '其',
    '这个', '那个', '什么', '怎么', '如何', '为什么', '可以', '可能', '应该', '需要',
})


def _tokenize(text):
    """中文分词，过滤停用词和短词"""
    words = jieba.cut(text)
    return [w for w in words if len(w) > 1 and w.strip() and w not in STOP_WORDS]


class EmbeddingService:
    """向量化服务类"""

    def __init__(self):
        self._dim = int(os.getenv('EMBEDDING_DIM', '256'))
        self._vocab_size = 20000
        self._lock = threading.Lock()
        self._idf = None
        self._vocab = None
        self._svd = None
        self._fitted = False

    def _build_vocab(self, texts):
        """从文本构建词表和IDF权重"""
        from collections import Counter

        word_freq = Counter()
        doc_freq = Counter()
        n_docs = len(texts)

        for text in texts:
            words = set(_tokenize(text))
            word_freq.update(words)
            doc_freq.update(words)

        # 按频率排序取 top N
        common = word_freq.most_common(self._vocab_size)
        self._vocab = {w: i for i, (w, _) in enumerate(common)}

        # 计算 IDF
        self._idf = np.zeros(len(self._vocab))
        for w, i in self._vocab.items():
            df = doc_freq.get(w, 0)
            self._idf[i] = np.log((n_docs + 1) / (df + 1)) + 1

        info(f"词表构建完成: {len(self._vocab)} 词")

    def _text_to_tfidf(self, text):
        """将文本转为 TF-IDF 向量"""
        words = _tokenize(text)
        vec = np.zeros(len(self._vocab), dtype=np.float32)

        word_count = {}
        for w in words:
            word_count[w] = word_count.get(w, 0) + 1

        for w, count in word_count.items():
            if w in self._vocab:
                idx = self._vocab[w]
                tf = count / len(words) if words else 0
                vec[idx] = tf * self._idf[idx]

        return vec

    def fit(self, corpus):
        """
        用语料库训练 TF-IDF + SVD 模型

        参数：
        - corpus: 文本列表，建议 100+ 条
        """
        with self._lock:
            from sklearn.decomposition import TruncatedSVD
            from sklearn.preprocessing import normalize

            info(f"开始训练 embedding 模型，语料 {len(corpus)} 条")

            self._build_vocab(corpus)

            # 构建 TF-IDF 矩阵
            tfidf_matrix = np.array([self._text_to_tfidf(t) for t in corpus])

            # SVD 降维
            n_components = min(self._dim, tfidf_matrix.shape[1] - 1, tfidf_matrix.shape[0] - 1)
            self._svd = TruncatedSVD(n_components=n_components, random_state=42)
            self._svd.fit(tfidf_matrix)

            self._fitted = True
            self._dim = n_components
            info(f"Embedding 模型训练完成 (dim={n_components})")

    def _vectorize(self, text):
        """将文本转为低维向量"""
        if not self._fitted:
            # 未训练时使用哈希回退
            return self._hash_fallback(text)

        tfidf = self._text_to_tfidf(text).reshape(1, -1)
        vec = self._svd.transform(tfidf)[0]

        # L2 归一化
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def _hash_fallback(self, text):
        """哈希回退方案（模型未训练时使用）"""
        vec = np.zeros(self._dim, dtype=np.float32)

        words = _tokenize(text)
        for w in words:
            h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
            idx = h % self._dim
            sign = 1 if (h // self._dim) % 2 == 0 else -1
            vec[idx] += sign

        # 字符 bigram
        chars = [c for c in text if c.strip()]
        for i in range(len(chars) - 1):
            bg = chars[i] + chars[i + 1]
            h = int(hashlib.md5(bg.encode('utf-8')).hexdigest(), 16)
            idx = h % self._dim
            sign = 1 if (h // self._dim) % 2 == 0 else -1
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec.tolist()

    def get_embedding(self, text, model=None):
        """
        获取文本的向量表示

        参数：
        - text: 要向量化的文本

        返回：
        - list: 向量数组
        """
        try:
            text = text[:8000]
            if not text.strip():
                return [0.0] * self._dim
            return self._vectorize(text)
        except Exception as e:
            error(f"获取向量失败：{e!s}")
            return None

    def get_embeddings(self, texts):
        """
        批量获取文本的向量表示
        """
        try:
            return [self._vectorize(t) if t and t.strip() else [0.0] * self._dim for t in texts]
        except Exception as e:
            error(f"批量获取向量失败：{e!s}")
            return None

    def cosine_similarity(self, vec1, vec2):
        """计算余弦相似度"""
        try:
            if vec1 is None or vec2 is None:
                return 0.0
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
        except Exception as e:
            error(f"计算相似度失败：{e!s}")
            return 0.0


# 全局实例
embedding_service = EmbeddingService()
