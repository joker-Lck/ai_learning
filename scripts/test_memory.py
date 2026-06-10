"""
记忆系统测试脚本
测试记忆存储、检索、遗忘、冲突修正等功能
"""

import os
import sys
import json

# 确保项目根目录在 sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv
load_dotenv()

from services.memory_service import memory_service
from services.memory_extractor import memory_extractor


def test_memory_system():
    """测试记忆系统"""
    print("=" * 60)
    print("记忆系统测试")
    print("=" * 60)
    
    user_id = 1  # 测试用户 ID
    
    with memory_service as ms:
        # 1. 测试短期记忆
        print("\n📝 测试短期记忆...")
        ms.add_short_term(user_id, "test_session", "user", "什么是机器学习？")
        ms.add_short_term(user_id, "test_session", "assistant", "机器学习是人工智能的一个分支...")
        context = ms.get_short_term_context(user_id, "test_session")
        print(f"  ✅ 短期记忆: {len(context)} 条")
        
        # 2. 测试情景记忆
        print("\n🎬 测试情景记忆...")
        ep_id = ms.add_episodic(
            user_id=user_id,
            episode_type="conversation",
            title="机器学习入门问答",
            summary="用户询问机器学习的基本概念",
            content="Q: 什么是机器学习？\nA: 机器学习是...",
            context={"subject": "机器学习"},
            importance=0.7
        )
        print(f"  ✅ 情景记忆 ID: {ep_id}")
        
        # 3. 测试语义记忆（事实知识）
        print("\n📚 测试语义记忆...")
        facts = [
            ("用户", "喜欢", "机器学习", 0.9),
            ("用户", "学习", "Python", 0.8),
            ("Python", "是", "编程语言", 0.95),
            ("机器学习", "包含", "监督学习", 0.9),
        ]
        
        for subject, predicate, obj, confidence in facts:
            fact_id = ms.add_semantic(
                user_id=user_id,
                fact_type="knowledge",
                subject=subject,
                predicate=predicate,
                object_val=obj,
                confidence=confidence
            )
            print(f"  ✅ 语义记忆: {subject} {predicate} {obj} (ID: {fact_id})")
            
        # 4. 测试实体记忆
        print("\n🏷️ 测试实体记忆...")
        entities = [
            ("skill", "Python", "编程语言", {"level": "intermediate"}),
            ("skill", "机器学习", "AI分支", {"level": "beginner"}),
            ("course", "CS229", "斯坦福机器学习课程", {}),
        ]
        
        entity_ids = {}
        for etype, ename, edesc, eattrs in entities:
            eid = ms.add_entity(
                user_id=user_id,
                entity_type=etype,
                entity_name=ename,
                description=edesc,
                attributes=eattrs
            )
            entity_ids[ename] = eid
            print(f"  ✅ 实体记忆: {ename} (ID: {eid})")
            
        # 5. 测试实体关系
        print("\n🔗 测试实体关系...")
        if "Python" in entity_ids and "机器学习" in entity_ids:
            rel_id = ms.add_relation(
                user_id=user_id,
                source_entity_id=entity_ids["Python"],
                target_entity_id=entity_ids["机器学习"],
                relation_type="used_for",
                relation_label="用于实现"
            )
            print(f"  ✅ 实体关系: Python -> 机器学习 (ID: {rel_id})")
            
        # 6. 测试搜索
        print("\n🔍 测试搜索功能...")
        
        # 搜索语义记忆
        results = ms.search_semantic(user_id, "机器学习")
        print(f"  ✅ 搜索语义记忆 '机器学习': {len(results)} 条")
        
        # 搜索实体
        results = ms.search_entities(user_id, "Python")
        print(f"  ✅ 搜索实体 'Python': {len(results)} 条")
        
        # 搜索情景记忆
        results = ms.search_episodic(user_id, "入门")
        print(f"  ✅ 搜索情景记忆 '入门': {len(results)} 条")
        
        # 7. 测试遗忘曲线
        print("\n⏰ 测试遗忘曲线...")
        forget_result = ms.apply_forgetting_curve(user_id)
        print(f"  ✅ 遗忘曲线: 遗忘 {forget_result['forgotten']} 条, 保留 {forget_result['reinforced']} 条")
        
        # 8. 测试冲突检测
        print("\n⚠️ 测试冲突检测...")
        # 添加一个冲突的事实
        ms.add_semantic(
            user_id=user_id,
            fact_type="preference",
            subject="用户",
            predicate="喜欢",
            object_val="深度学习",  # 之前是"机器学习"
            confidence=0.8
        )
        
        conflicts = ms.get_pending_conflicts(user_id)
        print(f"  ✅ 待解决冲突: {len(conflicts)} 条")
        
        # 解决冲突
        if conflicts:
            success = ms.resolve_conflict(conflicts[0]['id'], 'merge', user_id)
            print(f"  ✅ 冲突解决: {'成功' if success else '失败'}")
            
        # 9. 测试记忆统计
        print("\n📊 记忆统计:")
        stats = ms.get_memory_stats(user_id)
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)


def test_memory_extractor():
    """测试记忆提取器"""
    print("\n" + "=" * 60)
    print("记忆提取器测试")
    print("=" * 60)
    
    # 测试规则提取
    test_texts = [
        "我是计算机专业的学生，我喜欢机器学习",
        "我在学习Python编程，已经掌握了基础语法",
        "我想成为一名AI工程师，擅长深度学习",
        "TensorFlow是谷歌开发的深度学习框架"
    ]
    
    for text in test_texts:
        print(f"\n📝 文本: {text}")
        
        facts = memory_extractor.extract_facts_from_text(text)
        if facts:
            print(f"  事实: {json.dumps(facts, ensure_ascii=False, indent=2)}")
            
        entities = memory_extractor.extract_entities_from_text(text)
        if entities:
            print(f"  实体: {json.dumps(entities, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    test_memory_system()
    test_memory_extractor()
