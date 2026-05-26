"""
内容安全与防幻觉服务
提供敏感词过滤、事实核查、学术规范性检查等功能
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from core.logger import info, error, warning


class ContentSafetyService:
    """内容安全服务 - 过滤敏感和违规内容"""
    
    def __init__(self):
        # 敏感词库(示例,实际应使用更完整的词库)
        self.sensitive_words = self._load_sensitive_words()
        # 学术不规范模式
        self.academic_irregular_patterns = self._load_academic_patterns()
        info("内容安全服务初始化完成")
    
    def check_content_safety(self, content: str) -> Dict:
        """
        检查内容安全性
        
        Args:
            content: 待检查的文本内容
            
        Returns:
            {
                "is_safe": bool,
                "violations": [...],  # 违规项列表
                "risk_level": "low/medium/high",
                "suggestions": [...]  # 修改建议
            }
        """
        violations = []
        risk_level = "low"
        
        # 1. 敏感词检测
        sensitive_hits = self._detect_sensitive_words(content)
        if sensitive_hits:
            violations.append({
                "type": "sensitive_words",
                "items": sensitive_hits,
                "severity": "high"
            })
            risk_level = "high"
        
        # 2. 违规内容检测
        violation_hits = self._detect_policy_violations(content)
        if violation_hits:
            violations.append({
                "type": "policy_violations",
                "items": violation_hits,
                "severity": "high"
            })
            risk_level = "high"
        
        # 3. 学术不规范检测
        irregular_hits = self._detect_academic_irregularities(content)
        if irregular_hits:
            violations.append({
                "type": "academic_irregularities",
                "items": irregular_hits,
                "severity": "medium"
            })
            if risk_level == "low":
                risk_level = "medium"
        
        # 4. 生成修改建议
        suggestions = self._generate_suggestions(violations)
        
        result = {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "risk_level": risk_level,
            "suggestions": suggestions,
            "checked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if not result["is_safe"]:
            warning(f"内容安全检查发现 {len(violations)} 个问题")
        
        return result
    
    def filter_and_clean(self, content: str) -> Dict:
        """
        过滤并清理内容
        
        Args:
            content: 原始内容
            
        Returns:
            {
                "filtered_content": str,
                "removed_items": [...],
                "is_modified": bool
            }
        """
        original_content = content
        removed_items = []
        
        # 1. 移除敏感词
        for word in self.sensitive_words:
            if word in content:
                content = content.replace(word, "***")
                removed_items.append({"type": "sensitive_word", "original": word})
        
        # 2. 移除不当表达
        inappropriate_patterns = [
            (r'绝对正确', '较为准确'),
            (r'毫无疑问', '通常情况下'),
            (r'所有人都知道', '普遍认为'),
        ]
        
        for pattern, replacement in inappropriate_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                removed_items.append({
                    "type": "inappropriate_expression",
                    "original": pattern,
                    "replaced_with": replacement
                })
        
        result = {
            "filtered_content": content,
            "removed_items": removed_items,
            "is_modified": content != original_content
        }
        
        return result
    
    def _load_sensitive_words(self) -> List[str]:
        """加载敏感词库"""
        # 实际应从配置文件或数据库加载
        return [
            # 政治敏感
            "敏感词汇1",
            "敏感词汇2",
            # 暴力恐怖
            "暴力词汇1",
            # 色情低俗
            "色情词汇1",
            # 其他违规
            "违规词汇1",
        ]
    
    def _load_academic_patterns(self) -> List[Dict]:
        """加载学术不规范模式"""
        return [
            {
                "pattern": r"(?:绝对|肯定|必然|毫无疑问)\w{0,5}(?:正确|对|成立)",
                "description": "避免绝对化表述",
                "suggestion": "建议使用'通常''大多数情况下'等相对表述"
            },
            {
                "pattern": r"(?:所有人|大家都|众所周知)",
                "description": "避免过度概括",
                "suggestion": "建议提供具体数据来源或研究依据"
            },
            {
                "pattern": r"(?:最新|首创|第一|最好)\w{0,10}(?:技术|方法|成果)",
                "description": "避免夸大宣传",
                "suggestion": "建议客观描述,提供对比数据"
            }
        ]
    
    def _detect_sensitive_words(self, content: str) -> List[str]:
        """检测敏感词"""
        hits = []
        for word in self.sensitive_words:
            if word in content:
                hits.append(word)
        return hits
    
    def _detect_policy_violations(self, content: str) -> List[Dict]:
        """检测违规内容"""
        violations = []
        
        # 检测仇恨言论
        hate_patterns = [
            r"(?:歧视|侮辱|攻击)\w{0,10}(?:群体|民族|宗教)",
        ]
        for pattern in hate_patterns:
            if re.search(pattern, content):
                violations.append({
                    "type": "hate_speech",
                    "pattern": pattern,
                    "severity": "high"
                })
        
        # 检测虚假信息特征
        fake_news_patterns = [
            r"(?:震惊|爆料|内部消息|独家揭秘)",
        ]
        for pattern in fake_news_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append({
                    "type": "misinformation_indicator",
                    "pattern": pattern,
                    "severity": "medium"
                })
        
        return violations
    
    def _detect_academic_irregularities(self, content: str) -> List[Dict]:
        """检测学术不规范"""
        irregularities = []
        
        for item in self.academic_irregular_patterns:
            if re.search(item["pattern"], content):
                irregularities.append({
                    "pattern": item["pattern"],
                    "description": item["description"],
                    "suggestion": item["suggestion"]
                })
        
        return irregularities
    
    def _generate_suggestions(self, violations: List[Dict]) -> List[str]:
        """生成修改建议"""
        suggestions = []
        
        for violation in violations:
            if violation["type"] == "sensitive_words":
                suggestions.append("请移除或替换敏感词汇")
            elif violation["type"] == "policy_violations":
                suggestions.append("请确保内容符合政策法规要求")
            elif violation["type"] == "academic_irregularities":
                for item in violation["items"]:
                    suggestions.append(f"学术规范: {item['suggestion']}")
        
        return suggestions


class AntiHallucinationService:
    """防幻觉服务 - 减少AI生成内容的错误"""
    
    def __init__(self):
        info("防幻觉服务初始化完成")
    
    def verify_with_rag(self, 
                       claim: str, 
                       knowledge_context: str,
                       threshold: float = 0.7) -> Dict:
        """
        基于RAG知识库验证事实
        
        Args:
            claim: 需要验证的陈述
            knowledge_context: 相关知识库上下文
            threshold: 可信度阈值
            
        Returns:
            {
                "is_verified": bool,
                "confidence": float,
                "evidence": [...],
                "contradictions": [...]
            }
        """
        # 简化版:检查关键信息是否在知识库中
        evidence = []
        contradictions = []
        
        # 提取claim中的关键实体
        key_entities = self._extract_key_entities(claim)
        
        # 在知识库上下文中查找证据
        for entity in key_entities:
            if entity.lower() in knowledge_context.lower():
                evidence.append({
                    "entity": entity,
                    "found_in_context": True
                })
            else:
                contradictions.append({
                    "entity": entity,
                    "not_found": True,
                    "warning": "该实体未在知识库中找到,可能存在幻觉"
                })
        
        # 计算置信度
        total = len(key_entities)
        verified = len(evidence)
        confidence = verified / total if total > 0 else 0.5
        
        result = {
            "is_verified": confidence >= threshold,
            "confidence": round(confidence, 2),
            "evidence": evidence,
            "contradictions": contradictions,
            "verified_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if not result["is_verified"]:
            warning(f"事实验证失败,置信度: {confidence}")
        
        return result
    
    def add_citations(self, content: str, sources: List[Dict]) -> str:
        """
        为内容添加引用标注
        
        Args:
            content: 原始内容
            sources: 引用来源列表
            
        Returns:
            带引用的内容
        """
        if not sources:
            return content
        
        # 在内容末尾添加引用
        citations_text = "\n\n---\n**参考资料:**\n"
        for i, source in enumerate(sources, 1):
            citations_text += f"{i}. {source.get('title', '未命名')}"
            if source.get('author'):
                citations_text += f" - {source['author']}"
            if source.get('year'):
                citations_text += f" ({source['year']})"
            citations_text += "\n"
        
        return content + citations_text
    
    def detect_uncertainty_markers(self, content: str) -> List[Dict]:
        """
        检测不确定性标记,提示可能的幻觉
        
        Returns:
            不确定性表述列表
        """
        uncertainty_patterns = [
            (r"(?:可能|也许|或许|大概)\w{0,10}", "推测性表述"),
            (r"(?:据说|传言|听说)", "传闻性表述"),
            (r"(?:似乎|好像|看起来)", "模糊性表述"),
        ]
        
        markers = []
        for pattern, description in uncertainty_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                markers.append({
                    "text": match,
                    "type": description,
                    "suggestion": "建议核实信息来源,提供更准确的表述"
                })
        
        return markers
    
    def cross_validate(self, 
                      primary_answer: str,
                      alternative_sources: List[str]) -> Dict:
        """
        交叉验证 - 对比多个来源的一致性
        
        Args:
            primary_answer: 主要答案
            alternative_sources: 替代来源列表
            
        Returns:
            一致性分析结果
        """
        consistency_scores = []
        
        for source in alternative_sources:
            # 简化的相似度计算
            similarity = self._calculate_text_similarity(primary_answer, source)
            consistency_scores.append({
                "source_preview": source[:50] + "...",
                "similarity": round(similarity, 2)
            })
        
        avg_consistency = sum(s["similarity"] for s in consistency_scores) / len(consistency_scores) if consistency_scores else 0
        
        return {
            "average_consistency": round(avg_consistency, 2),
            "sources_checked": len(consistency_scores),
            "details": consistency_scores,
            "is_consistent": avg_consistency >= 0.6
        }
    
    def _extract_key_entities(self, text: str) -> List[str]:
        """提取关键实体(简化版)"""
        # 实际应使用NER模型
        # 这里简单提取名词短语
        entities = []
        
        # 提取引号内的内容
        quoted = re.findall(r'"([^"]*)"', text)
        entities.extend(quoted)
        
        # 提取专有名词(大写字母开头的词)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', text)
        entities.extend(proper_nouns)
        
        # 去重
        return list(set(entities))
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度(简化版Jaccard相似度)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)


# 全局服务实例
content_safety_service = ContentSafetyService()
anti_hallucination_service = AntiHallucinationService()
