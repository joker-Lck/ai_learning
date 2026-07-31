"""
Self-RAG / CRAG 检索决策层
- 前置判断：问题是否需要检索
- 策略路由：按题型自动选择最优检索策略
- 后置校验：检索结果是否真正回答了问题
"""

import re

from core.logger import debug, error, info, warning


class SelfRAG:
    """
    Self-RAG 检索决策器

    三层决策：
    1. retrieval_gate: 判断是否需要检索
    2. strategy_router: 选择检索策略
    3. result_verifier: 验证检索结果质量
    """

    # 简单问题模式（不需要检索）
    SIMPLE_PATTERNS = [
        r'^(你好|hi|hello|嗨|hey)',
        r'^(谢谢|感谢|多谢|thanks)',
        r'^(再见|拜拜|bye)',
        r'^(你是谁|你叫什么|你是什么)',
        r'^\d+[\+\-\*\/]\d+',  # 简单算术
        r'^(今天|明天|昨天).*(几号|星期|天气)',
    ]

    # 代码题关键词
    CODE_KEYWORDS = [
        '代码', '函数', '编程', '程序', 'python', 'java', 'c++', 'javascript',
        '算法', '实现', '编写', '写一个', '写代码', '代码实现', '怎么写',
        'def ', 'class ', 'import ', 'function', '变量', '循环', '递归',
        '数组', '列表', '字典', '排序', '查找', '数据结构',
    ]

    # 概念题关键词
    CONCEPT_KEYWORDS = [
        '什么是', '定义', '概念', '原理', '理论', '含义', '意思',
        '解释', '介绍', '概述', '区别', '比较', '异同', '优缺点',
        '为什么', '原因', '意义', '作用', '特点', '性质',
    ]

    # 推导题关键词
    DERIVATION_KEYWORDS = [
        '推导', '证明', '计算', '求解', '解题', '步骤', '过程',
        '怎么推', '如何证', '怎么算', '如何求', '公式推导',
        '由.*推出', '从.*到', '推导过程', '证明过程',
    ]

    # 应用题关键词
    APPLICATION_KEYWORDS = [
        '应用', '实例', '举例', '案例', '场景', '实际',
        '如何用', '怎么用', '应用于', '实践', '工程',
        '项目', '开发', '实现', '部署',
    ]

    def __init__(self):
        self._qa_service = None

    @property
    def qa_service(self):
        if self._qa_service is None:
            from services.qa_service import qa_service
            self._qa_service = qa_service
        return self._qa_service

    def retrieval_gate(self, question: str, subject: str = "综合") -> dict:
        """
        判断问题是否需要检索

        返回:
        {
            "needs_retrieval": bool,
            "confidence": float,
            "reason": str,
            "direct_answer": str | None  # 不需要检索时的直接回答
        }
        """
        q = question.strip()

        # 1. 简单模式匹配
        for pattern in self.SIMPLE_PATTERNS:
            if re.search(pattern, q, re.IGNORECASE):
                return {
                    "needs_retrieval": False,
                    "confidence": 0.95,
                    "reason": "simple_pattern",
                    "direct_answer": self._generate_simple_reply(q),
                }

        # 2. 太短的问题（<5字符）可能不需要检索
        if len(q) < 5:
            return {
                "needs_retrieval": False,
                "confidence": 0.7,
                "reason": "too_short",
                "direct_answer": None,  # 让 LLM 直接回答
            }

        # 3. 纯问候/闲聊检测（用规则而非 LLM，节省调用）
        chat_patterns = [
            r'^(今天|最近|现在).*(怎么样|好吗|如何)',
            r'(无聊|累|烦|开心|高兴|难过)',
            r'(聊聊|聊天|说说话)',
        ]
        for pattern in chat_patterns:
            if re.search(pattern, q):
                return {
                    "needs_retrieval": False,
                    "confidence": 0.8,
                    "reason": "chitchat",
                    "direct_answer": None,
                }

        # 4. 默认需要检索
        return {
            "needs_retrieval": True,
            "confidence": 0.9,
            "reason": "knowledge_question",
            "direct_answer": None,
        }

    def strategy_router(self, question: str, subject: str = "综合") -> dict:
        """
        按题型自动选择检索策略

        返回:
        {
            "strategy": str,  # hyde/multi_query/rag_fusion/multi_hop/graph/hybrid
            "question_type": str,  # code/concept/derivation/application/general
            "confidence": float,
            "reason": str
        }
        """
        q = question.lower().strip()

        # 代码题 → KNN 关键词检索（代码术语精确匹配更好）
        code_score = sum(1 for kw in self.CODE_KEYWORDS if kw in q)
        if code_score >= 2 or any(kw in q for kw in ['代码', '编程', '写一个', '实现']):
            return {
                "strategy": "hybrid",
                "question_type": "code",
                "confidence": 0.85,
                "reason": f"代码题关键词命中={code_score}",
            }

        # 概念题 → HyDE（生成假设答案扩展语义）
        concept_score = sum(1 for kw in self.CONCEPT_KEYWORDS if kw in q)
        if concept_score >= 2 or any(kw in q for kw in ['什么是', '定义', '概念', '原理']):
            return {
                "strategy": "hyde",
                "question_type": "concept",
                "confidence": 0.85,
                "reason": f"概念题关键词命中={concept_score}",
            }

        # 推导题 → ReAct（推理-检索交替，更适合多步骤推导）
        derivation_score = sum(1 for kw in self.DERIVATION_KEYWORDS if kw in q)
        if derivation_score >= 2 or any(kw in q for kw in ['推导', '证明', '计算过程']):
            return {
                "strategy": "react",
                "question_type": "derivation",
                "confidence": 0.85,
                "reason": f"推导题关键词命中={derivation_score}",
            }

        # 应用题 → Graph-Enhanced（知识图谱关联）
        app_score = sum(1 for kw in self.APPLICATION_KEYWORDS if kw in q)
        if app_score >= 2:
            return {
                "strategy": "graph",
                "question_type": "application",
                "confidence": 0.75,
                "reason": f"应用题关键词命中={app_score}",
            }

        # 短查询 → HyDE（扩展语义）
        if len(q) < 15:
            return {
                "strategy": "hyde",
                "question_type": "short",
                "confidence": 0.7,
                "reason": "短查询，使用HyDE扩展",
            }

        # 长查询 → RAG-Fusion（多查询融合）
        if len(q) >= 30:
            return {
                "strategy": "rag_fusion",
                "question_type": "complex",
                "confidence": 0.7,
                "reason": "长查询，使用RAG-Fusion融合",
            }

        # 默认 → 混合检索
        return {
            "strategy": "hybrid",
            "question_type": "general",
            "confidence": 0.6,
            "reason": "通用问题，使用混合检索",
        }

    def result_verifier(self, question: str, retrieved_docs: list,
                        answer: str) -> dict:
        """
        后置校验：检索结果是否真正回答了问题

        返回:
        {
            "is_sufficient": bool,
            "quality_score": float,  # 0-1
            "should_retry": bool,
            "retry_strategy": str | None,
            "reason": str
        }
        """
        if not retrieved_docs:
            return {
                "is_sufficient": False,
                "quality_score": 0.0,
                "should_retry": True,
                "retry_strategy": "hyde",
                "reason": "未检索到任何文档",
            }

        # 简单规则校验
        q_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', question.lower()))
        a_words = set(re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}', answer.lower()))

        # 答案与问题的词汇重叠度
        overlap = q_words & a_words
        overlap_ratio = len(overlap) / max(len(q_words), 1)

        # 检索文档的相关性
        doc_scores = [d.get('score', d.get('rrf_score', d.get('similarity', 0))) for d in retrieved_docs]
        avg_score = sum(doc_scores) / max(len(doc_scores), 1)

        # 综合判断
        quality_score = 0.0
        quality_score += min(overlap_ratio * 2, 0.4)  # 词汇重叠贡献最多0.4
        quality_score += min(avg_score * 0.6, 0.6)    # 检索分数贡献最多0.6

        is_sufficient = quality_score >= 0.3
        should_retry = quality_score < 0.2 and len(retrieved_docs) < 3

        # 选择重试策略
        retry_strategy = None
        if should_retry:
            if len(question) < 15:
                retry_strategy = "rag_fusion"  # 短查询换 RAG-Fusion
            else:
                retry_strategy = "multi_hop"   # 长查询换 Multi-Hop

        return {
            "is_sufficient": is_sufficient,
            "quality_score": round(quality_score, 3),
            "should_retry": should_retry,
            "retry_strategy": retry_strategy,
            "reason": f"quality={quality_score:.3f}, overlap={overlap_ratio:.2f}, avg_score={avg_score:.3f}",
        }

    def _generate_simple_reply(self, question: str) -> str:
        """生成简单问题的直接回复"""
        q = question.strip().lower()
        if re.search(r'^(你好|hi|hello|嗨|hey)', q):
            return "你好！我是你的学习助手，有什么学习上的问题可以问我。"
        if re.search(r'^(谢谢|感谢|多谢|thanks)', q):
            return "不客气！如果还有其他问题，随时可以问我。"
        if re.search(r'^(再见|拜拜|bye)', q):
            return "再见！祝你学习顺利！"
        if re.search(r'^(你是谁|你叫什么|你是什么)', q):
            return "我是一个AI学习助手，可以帮助你解答学习问题、生成学习资源、规划学习路径。"
        return ""


# 全局单例
self_rag = SelfRAG()
