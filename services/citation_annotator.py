"""
答案引用标注 — 对关键声明标注来源文档
纯规则实现（Jaccard 相似度），零 LLM 调用
"""

import re
from dataclasses import dataclass

from core.logger import info

_STOP = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都",
         "一", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
         "没有", "看", "好", "自己", "这", "他", "她", "它", "吗", "什么", "怎么"}


@dataclass
class CitationResult:
    """引用标注结果"""
    annotated_text: str         # 标注后的文本
    citation_count: int         # 引用数量
    source_map: dict            # 引用编号 → 文档摘要


class CitationAnnotator:
    """答案引用标注器"""

    def __init__(self, similarity_threshold: float = 0.35):
        self.threshold = similarity_threshold

    def annotate(self, answer: str, retrieved_docs: list[dict]) -> CitationResult:
        """对答案中的关键声明标注来源"""
        if not retrieved_docs:
            return CitationResult(
                annotated_text=answer,
                citation_count=0,
                source_map={},
            )

        # 1. 预处理检索文档：提取关键句子
        doc_sentences: list[tuple[str, int]] = []  # (sentence, doc_index)
        source_map: dict[int, str] = {}

        for i, doc in enumerate(retrieved_docs):
            content = doc.get("content", "")
            title = doc.get("title", f"文档{i + 1}")
            source_map[i + 1] = title[:50]

            # 按句号/换行分句
            sentences = re.split(r'[。！？\n]', content)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) >= 10:
                    doc_sentences.append((sent, i))

        if not doc_sentences:
            return CitationResult(
                annotated_text=answer,
                citation_count=0,
                source_map=source_map,
            )

        # 2. 对答案中的句子逐句匹配
        answer_sentences = re.split(r'(?<=[。！？\n])', answer)
        annotated_parts = []
        citation_count = 0

        for sent in answer_sentences:
            sent = sent.strip()
            if not sent or len(sent) < 5:
                annotated_parts.append(sent)
                continue

            # 计算与每个文档句子的 Jaccard 相似度
            best_doc_idx = -1
            best_score = 0.0

            sent_words = self._tokenize(sent)

            for doc_sent, doc_idx in doc_sentences:
                doc_words = self._tokenize(doc_sent)
                jaccard = self._jaccard(sent_words, doc_words)
                if jaccard > best_score:
                    best_score = jaccard
                    best_doc_idx = doc_idx

            # 高相似度 → 标注来源
            if best_score >= self.threshold and best_doc_idx >= 0:
                citation_num = best_doc_idx + 1
                annotated_parts.append(f"{sent} [^{citation_num}]")
                citation_count += 1
            else:
                annotated_parts.append(sent)

        annotated_text = "".join(annotated_parts)

        info(f"引用标注: {citation_count}处引用, {len(retrieved_docs)}个源文档")

        return CitationResult(
            annotated_text=annotated_text,
            citation_count=citation_count,
            source_map=source_map,
        )

    def _tokenize(self, text: str) -> set:
        """分词（中英文混合）"""
        words = set()
        for char in text:
            if '\u4e00' <= char <= '\u9fff' and char not in _STOP:
                words.add(char)
        for word in re.findall(r'[a-zA-Z]{2,}', text.lower()):
            words.add(word)
        return words

    def _jaccard(self, set_a: set, set_b: set) -> float:
        """Jaccard 相似度"""
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0


# 全局单例
citation_annotator = CitationAnnotator()
