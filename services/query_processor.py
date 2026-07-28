"""
查询预处理层 — 意图识别、实体识别、指代消解、拼写纠错
纯规则实现，零 LLM 调用
"""

import re
from dataclasses import dataclass, field

from core.logger import info

# 学科术语词典（从知识库动态构建 + 静态补充）
SUBJECT_TERMS = {
    "数学": {"微积分", "线性代数", "概率论", "矩阵", "导数", "积分", "极限", "微分方程", "级数", "特征值"},
    "数据结构": {"数组", "链表", "栈", "队列", "树", "二叉树", "图", "哈希", "堆", "排序", "遍历", "红黑树", "B树"},
    "机器学习": {"回归", "分类", "聚类", "神经网络", "梯度下降", "过拟合", "正则化", "损失函数", "反向传播", "SVM", "决策树"},
    "深度学习": {"卷积", "CNN", "RNN", "LSTM", "Transformer", "注意力机制", "GAN", "ResNet", "BERT", "GPT"},
    "计算机网络": {"TCP", "UDP", "IP", "HTTP", "DNS", "路由", "交换机", "三次握手", "四次挥手", "拥塞控制"},
    "操作系统": {"进程", "线程", "死锁", "内存管理", "虚拟内存", "分页", "调度", "文件系统", "中断"},
    "数据库": {"SQL", "索引", "事务", "范式", "JOIN", "主键", "外键", "B+树", "MVCC", "锁"},
    "Python": {"列表", "字典", "装饰器", "生成器", "迭代器", "异常", "类", "模块", "lambda", "推导式"},
    "英语": {"语法", "时态", "虚拟语气", "从句", "词汇", "阅读理解", "翻译", "写作"},
}

# 意图关键词
INTENT_PATTERNS = {
    "definition": ["什么是", "定义", "含义", "概念", "意思", "指的是", "是什么", "什么叫"],
    "comparison": ["区别", "对比", "比较", "不同", "差异", "vs", "和.*有什么"],
    "code": ["代码", "编程", "实现", "写一个", "怎么写", "如何实现", "程序", "函数", "算法", "python", "java", "c++"],
    "explanation": ["为什么", "原理", "怎么理解", "解释", "详细", "过程", "步骤", "如何"],
    "example": ["举例", "例子", "比如", "举个", "实例", "案例"],
    "practice": ["练习", "做题", "习题", "题目", "测试", "考试"],
}

# 停用词
STOP_WORDS = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很",
              "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
              "吗", "什么", "怎么", "如何", "请", "帮", "能", "可以", "给", "告诉"}


@dataclass
class ProcessedQuery:
    """处理后的查询"""
    original: str          # 原始查询
    corrected: str         # 纠错后
    intent: str            # 意图类型
    entities: dict         # 识别的实体 {"subject": "数据结构", "concept": "二叉树"}
    expanded_terms: list   # 扩展词
    suggested_strategy: str  # 建议检索策略
    confidence: float      # 处理置信度


class QueryProcessor:
    """查询预处理器"""

    def process(self, raw_query: str, conversation_history: list | None = None) -> ProcessedQuery:
        """完整处理流程"""
        # 1. 拼写纠错
        corrected = self._spell_correct(raw_query)

        # 2. 指代消解
        resolved = self._resolve_references(corrected, conversation_history or [])

        # 3. 意图分类
        intent, intent_conf = self._classify_intent(resolved)

        # 4. 实体识别
        entities = self._extract_entities(resolved)

        # 5. 查询扩展
        expanded = self._expand_query(entities)

        # 6. 策略建议
        strategy = self._suggest_strategy(intent, entities, len(resolved))

        result = ProcessedQuery(
            original=raw_query,
            corrected=resolved,
            intent=intent,
            entities=entities,
            expanded_terms=expanded,
            suggested_strategy=strategy,
            confidence=intent_conf,
        )

        info(f"Query处理: intent={intent}, entities={entities}, strategy={strategy}")
        return result

    def _spell_correct(self, text: str) -> str:
        """拼写纠错 — 基于学科术语词典的编辑距离匹配"""
        words = list(jieba.cut(text))
        corrected = []
        all_terms = set()
        for terms in SUBJECT_TERMS.values():
            all_terms.update(terms)

        for word in words:
            if len(word) >= 2 and word not in STOP_WORDS:
                # 检查是否接近某个学科术语
                best_match = self._find_closest_term(word, all_terms)
                if best_match and best_match != word:
                    corrected.append(best_match)
                    continue
            corrected.append(word)

        return "".join(corrected)

    def _find_closest_term(self, word: str, terms: set, max_dist: int = 1) -> str | None:
        """编辑距离匹配（仅对短词）"""
        if len(word) < 2 or len(word) > 10:
            return None
        for term in terms:
            if abs(len(term) - len(word)) > max_dist:
                continue
            if self._edit_distance(word, term) <= max_dist:
                return term
        return None

    @staticmethod
    def _edit_distance(s1: str, s2: str) -> int:
        """编辑距离"""
        if abs(len(s1) - len(s2)) > 1:
            return 2
        m, n = len(s1), len(s2)
        dp = list(range(n + 1))
        for i in range(1, m + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, n + 1):
                temp = dp[j]
                if s1[i - 1] == s2[j - 1]:
                    dp[j] = prev
                else:
                    dp[j] = 1 + min(prev, dp[j], dp[j - 1])
                prev = temp
        return dp[n]

    def _resolve_references(self, text: str, history: list) -> str:
        """指代消解 — 从上下文解析代词"""
        ref_patterns = {
            "它": 0, "他": 0, "这个": 0, "那个": 0,
            "上面": 0, "刚才": 0, "之前": 1,
        }

        needs_resolve = any(p in text for p in ref_patterns)
        if not needs_resolve or not history:
            return text

        # 从最近的助手回复中提取核心实体
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                content = msg.get("content", "")
                entities = self._extract_entities(content)
                concept = entities.get("concept")
                if concept:
                    # 简单替换：把"它"替换为最近提到的概念
                    for ref in ["它", "这个", "那个"]:
                        if ref in text:
                            text = text.replace(ref, concept, 1)
                            return text
                break

        return text

    def _classify_intent(self, text: str) -> tuple[str, float]:
        """意图分类 — 关键词匹配"""
        scores: dict[str, float] = {}

        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, text):
                    score += 1
            if score > 0:
                scores[intent] = score

        if not scores:
            # 默认：短查询→definition，长查询→explanation
            return ("definition" if len(text) < 20 else "explanation", 0.3)

        best = max(scores, key=scores.get)  # type: ignore
        confidence = min(scores[best] / 3, 1.0)
        return (best, confidence)

    def _extract_entities(self, text: str) -> dict:
        """实体识别 — 学科术语词典匹配"""
        entities: dict = {}

        # 识别学科
        for subject, terms in SUBJECT_TERMS.items():
            if subject in text:
                entities["subject"] = subject
                break

        # 识别概念（从所有术语中匹配）
        found_concepts = []
        all_terms = set()
        for terms in SUBJECT_TERMS.values():
            all_terms.update(terms)

        for term in sorted(all_terms, key=len, reverse=True):
            if term in text and term not in STOP_WORDS:
                found_concepts.append(term)
                if len(found_concepts) >= 3:
                    break

        if found_concepts:
            entities["concept"] = found_concepts[0]
            entities["concepts"] = found_concepts

        return entities

    def _expand_query(self, entities: dict) -> list:
        """查询扩展 — 同义词 + 相关概念"""
        expanded = []
        concept = entities.get("concept", "")
        subject = entities.get("subject", "")

        if concept:
            expanded.append(concept)

        # 从学科术语中找相关概念
        if subject and subject in SUBJECT_TERMS:
            related = SUBJECT_TERMS[subject] - {concept}
            expanded.extend(list(related)[:3])

        return expanded

    def _suggest_strategy(self, intent: str, entities: dict, query_len: int) -> str:
        """建议检索策略 — 复用 self_rag 的路由逻辑"""
        if intent == "code":
            return "hybrid"
        elif intent == "definition":
            return "hyde"
        elif intent == "comparison":
            return "rag_fusion"
        elif query_len < 15:
            return "hyde"
        elif query_len > 100:
            return "rag_fusion"
        else:
            return "hybrid"


# 全局单例
query_processor = QueryProcessor()

# jieba 延迟导入
try:
    import jieba
except ImportError:
    jieba = None  # type: ignore
    import re as _re

    class _JiebaFallback:
        """jieba 不可用时的简单分词"""
        def cut(self, text: str):
            # 按标点和空格分词
            return _re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+|\d+', text)

    jieba = _JiebaFallback()  # type: ignore
