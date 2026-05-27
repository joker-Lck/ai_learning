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
        """加载敏感词库 — 覆盖 8 大类常见违规内容"""
        return [
            # ── 政治敏感 ──
            "台独", "藏独", "疆独", "港独", "分裂国家",
            "颠覆政权", "煽动颠覆", "反政府", "推翻政府",
            "六四", "天安门事件", "文化大革命",
            "法轮功", "法轮大法",
            "邪教组织",

            # ── 暴力恐怖 ──
            "恐怖袭击", "制造炸弹", "自制炸弹", "炸弹教程",
            "砍杀", "无差别杀人", "报复社会",
            "买枪", "贩卖枪支", "枪支交易",
            "砍刀", "管制刀具",
            "绑架勒索", "人质",

            # ── 色情低俗 ──
            "色情网站", "色情视频", "色情图片", "色情小说",
            "裸聊", "裸体直播", "成人视频",
            "卖淫", "嫖娼", "援交",
            "性交易", "性服务",
            "淫秽", "淫乱",

            # ── 赌博毒品 ──
            "赌博网站", "网络赌博", "赌球", "赌马",
            "博彩平台", "彩票预测", "六合彩",
            "毒品交易", "贩毒", "吸毒",
            "冰毒", "海洛因", "大麻", "摇头丸",
            "制毒", "毒品配方",

            # ── 仇恨歧视 ──
            "种族歧视", "民族歧视", "地域歧视",
            "性别歧视", "性别对立",
            "侮辱女性", "侮辱男性",
            "残疾人歧视", "歧视残障",
            "仇恨言论", "煽动仇恨",

            # ── 诈骗欺诈 ──
            "电信诈骗", "网络诈骗", "杀猪盘",
            "刷单返利", "刷单诈骗",
            "传销", "非法集资", "庞氏骗局",
            "洗钱", "地下钱庄",
            "钓鱼网站", "盗号", "盗取密码",

            # ── 脏话粗口 ──
            "他妈的", "你妈的", "草泥马", "卧槽",
            "傻逼", "煞笔", "沙比", "牛逼",
            "操你", "干你", "日你",
            "贱人", "贱货", "婊子",
            "狗日的", "王八蛋", "混蛋",

            # ── 自残自杀 ──
            "自杀方法", "自杀教程", "如何自杀",
            "割腕", "上吊", "跳楼",
            "安眠药", "服毒",
            "自残", "自我伤害",
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
            r"(?:歧视|侮辱|攻击|谩骂)\w{0,10}(?:群体|民族|宗教|种族)",
            r"(?:消灭|杀死|赶走)\w{0,6}(?:族|人|裔)",
            r"(?:劣等|低贱|野蛮)\w{0,4}(?:民族|种族|人)",
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
            r"(?:震惊|爆料|内部消息|独家揭秘|惊天内幕)",
            r"(?:不转不是|不看后悔|速转|紧急通知)",
            r"(?:官方已确认|国家已公布|央视报道)\w{0,20}(?:假|谣言|不实)",
        ]
        for pattern in fake_news_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                violations.append({
                    "type": "misinformation_indicator",
                    "pattern": pattern,
                    "severity": "medium"
                })

        # 检测违法指导内容
        illegal_guide_patterns = [
            r"(?:如何|怎么|教程)\w{0,8}(?:作弊|代考|替考)",
            r"(?:破解|盗取|获取)\w{0,8}(?:密码|账号|数据)",
            r"(?:制作|合成|伪造)\w{0,8}(?:证件|证书|学历|公章)",
        ]
        for pattern in illegal_guide_patterns:
            if re.search(pattern, content):
                violations.append({
                    "type": "illegal_guide",
                    "pattern": pattern,
                    "severity": "high"
                })

        # 检测商业推广/引流
        spam_patterns = [
            r"(?:加微信|加QQ|扫码领取|点击链接)\w{0,20}(?:免费|优惠|红包)",
            r"(?:日赚|月入|躺赚)\w{0,10}(?:元|万|钱)",
        ]
        for pattern in spam_patterns:
            if re.search(pattern, content):
                violations.append({
                    "type": "spam_promotion",
                    "pattern": pattern,
                    "severity": "low"
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
            vtype = violation.get("type", "")
            if vtype == "sensitive_words":
                suggestions.append("请移除或替换敏感词汇，确保内容合规")
            elif vtype == "policy_violations":
                suggestions.append("请确保内容符合政策法规要求")
            elif vtype == "hate_speech":
                suggestions.append("请避免仇恨言论，尊重不同群体")
            elif vtype == "misinformation_indicator":
                suggestions.append("请核实信息来源，避免传播未经证实的内容")
            elif vtype == "illegal_guide":
                suggestions.append("请勿发布违法操作指导内容")
            elif vtype == "spam_promotion":
                suggestions.append("请移除商业推广或引流内容")
            elif vtype == "academic_irregularities":
                for item in violation.get("items", []):
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
