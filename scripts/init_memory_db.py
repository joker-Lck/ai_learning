"""
无限长时记忆架构 - 记忆系统初始化
支持短期记忆、情景记忆、语义记忆、实体记忆、遗忘机制、冲突修正
"""

import mysql.connector
import json
from datetime import datetime


def get_memory_db_config():
    """获取记忆数据库配置"""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    return {
        'host': os.getenv('MEMORY_DB_HOST', 'localhost'),
        'port': int(os.getenv('MEMORY_DB_PORT', '3306')),
        'user': os.getenv('MEMORY_DB_USER', 'root'),
        'password': os.getenv('MEMORY_DB_PASSWORD', ''),
        'charset': 'utf8mb4'
    }


def create_memory_database():
    """创建记忆数据库"""
    config = get_memory_db_config()
    conn = mysql.connector.connect(**config, use_pure=True)
    cursor = conn.cursor()
    
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS ai_memory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ 数据库 'ai_memory' 创建成功!")
    finally:
        cursor.close()
        conn.close()


def init_memory_tables():
    """初始化记忆系统表结构"""
    config = get_memory_db_config()
    config['database'] = 'ai_memory'
    conn = mysql.connector.connect(**config, use_pure=True)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化记忆数据库 (ai_memory)...")
        
        # ==========================================
        # 1. 短期记忆表 - 最近对话上下文（Token 级别）
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS short_term_memory (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
                role ENUM('user', 'assistant', 'system') NOT NULL,
                content TEXT NOT NULL COMMENT '对话内容',
                token_count INT DEFAULT 0 COMMENT 'Token 数量',
                context_window_position INT DEFAULT 0 COMMENT '在上下文窗口中的位置',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_session (user_id, session_id),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='短期记忆：最近对话上下文'
        """)
        print("  ✅ 短期记忆表 (short_term_memory) 创建成功!")
        
        # ==========================================
        # 2. 情景记忆表 - 对话事件/场景
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                episode_type ENUM('conversation', 'learning', 'question', 'task', 'event') NOT NULL,
                title VARCHAR(255) COMMENT '情景标题',
                summary TEXT COMMENT '情景摘要',
                context JSON COMMENT '情景上下文（时间、地点、参与者等）',
                content TEXT COMMENT '情景详细内容',
                emotions JSON COMMENT '情绪状态',
                importance FLOAT DEFAULT 0.5 COMMENT '重要性评分 0-1',
                access_count INT DEFAULT 0 COMMENT '访问次数',
                last_accessed_at TIMESTAMP NULL COMMENT '最后访问时间',
                embedding BLOB COMMENT '向量嵌入',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_type (episode_type),
                INDEX idx_importance (importance),
                INDEX idx_last_accessed (last_accessed_at),
                FULLTEXT idx_content (title, summary, content)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='情景记忆：对话事件和场景'
        """)
        print("  ✅ 情景记忆表 (episodic_memory) 创建成功!")
        
        # ==========================================
        # 3. 语义记忆表 - 事实知识（向量存储）
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS semantic_memory (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                fact_type ENUM('preference', 'knowledge', 'skill', 'habit', 'goal', 'constraint') NOT NULL,
                subject VARCHAR(255) NOT NULL COMMENT '主题',
                predicate VARCHAR(255) NOT NULL COMMENT '谓词/关系',
                object TEXT NOT NULL COMMENT '客体/值',
                confidence FLOAT DEFAULT 0.8 COMMENT '置信度 0-1',
                source VARCHAR(255) COMMENT '来源（对话ID、文档等）',
                embedding BLOB COMMENT '向量嵌入',
                access_count INT DEFAULT 0,
                last_accessed_at TIMESTAMP NULL,
                is_verified BOOLEAN DEFAULT FALSE COMMENT '是否已验证',
                conflict_resolution JSON COMMENT '冲突解决记录',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_type (fact_type),
                INDEX idx_subject (subject),
                INDEX idx_confidence (confidence),
                UNIQUE KEY uk_spo (user_id, subject, predicate, object(255))
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='语义记忆：事实知识（SPO三元组）'
        """)
        print("  ✅ 语义记忆表 (semantic_memory) 创建成功!")
        
        # ==========================================
        # 4. 实体记忆表 - 实体画像（KV存储）
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_memory (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                entity_type ENUM('person', 'concept', 'skill', 'course', 'tool', 'organization', 'other') NOT NULL,
                entity_name VARCHAR(255) NOT NULL COMMENT '实体名称',
                entity_alias VARCHAR(255) COMMENT '实体别名',
                attributes JSON COMMENT '实体属性（KV结构）',
                description TEXT COMMENT '实体描述',
                importance FLOAT DEFAULT 0.5,
                access_count INT DEFAULT 0,
                last_accessed_at TIMESTAMP NULL,
                embedding BLOB COMMENT '向量嵌入',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_type (entity_type),
                INDEX idx_name (entity_name),
                UNIQUE KEY uk_user_entity (user_id, entity_type, entity_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实体记忆：实体画像KV存储'
        """)
        print("  ✅ 实体记忆表 (entity_memory) 创建成功!")
        
        # ==========================================
        # 5. 实体关系表 - 图谱结构
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_relations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                source_entity_id BIGINT NOT NULL,
                target_entity_id BIGINT NOT NULL,
                relation_type VARCHAR(100) NOT NULL COMMENT '关系类型',
                relation_label VARCHAR(255) COMMENT '关系标签',
                weight FLOAT DEFAULT 1.0 COMMENT '关系权重',
                context TEXT COMMENT '关系上下文',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_source (source_entity_id),
                INDEX idx_target (target_entity_id),
                INDEX idx_relation (relation_type),
                UNIQUE KEY uk_relation (user_id, source_entity_id, target_entity_id, relation_type),
                FOREIGN KEY (source_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE,
                FOREIGN KEY (target_entity_id) REFERENCES entity_memory(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实体关系：知识图谱'
        """)
        print("  ✅ 实体关系表 (entity_relations) 创建成功!")
        
        # ==========================================
        # 6. 记忆元数据表 - 遗忘机制
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_metadata (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                memory_type ENUM('short_term', 'episodic', 'semantic', 'entity', 'relation') NOT NULL,
                memory_id BIGINT NOT NULL COMMENT '对应记忆表的ID',
                user_id INT NOT NULL,
                importance FLOAT DEFAULT 0.5 COMMENT '重要性',
                decay_rate FLOAT DEFAULT 0.1 COMMENT '衰减速率',
                access_count INT DEFAULT 0,
                last_accessed_at TIMESTAMP NULL,
                is_forgotten BOOLEAN DEFAULT FALSE COMMENT '是否已被遗忘',
                forgotten_at TIMESTAMP NULL COMMENT '遗忘时间',
                reinforcement_count INT DEFAULT 0 COMMENT '强化次数',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_type (memory_type),
                INDEX idx_forgotten (is_forgotten),
                INDEX idx_importance (importance),
                UNIQUE KEY uk_memory (memory_type, memory_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='记忆元数据：遗忘机制控制'
        """)
        print("  ✅ 记忆元数据表 (memory_metadata) 创建成功!")
        
        # ==========================================
        # 7. 记忆冲突表 - 冲突修正
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_conflicts (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                conflict_type ENUM('fact_contradiction', 'preference_change', 'knowledge_update', 'temporal_conflict') NOT NULL,
                old_memory_type VARCHAR(50) NOT NULL,
                old_memory_id BIGINT NOT NULL,
                new_memory_type VARCHAR(50) NOT NULL,
                new_memory_id BIGINT NOT NULL,
                resolution_strategy ENUM('keep_old', 'keep_new', 'merge', 'manual') DEFAULT 'manual',
                resolution_result JSON COMMENT '解决结果',
                resolved BOOLEAN DEFAULT FALSE,
                resolved_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_resolved (resolved),
                INDEX idx_type (conflict_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='记忆冲突：冲突检测与修正'
        """)
        print("  ✅ 记忆冲突表 (memory_conflicts) 创建成功!")
        
        # ==========================================
        # 8. 记忆访问日志 - 用于分析遗忘曲线
        # ==========================================
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_access_log (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                memory_type VARCHAR(50) NOT NULL,
                memory_id BIGINT NOT NULL,
                access_type ENUM('read', 'write', 'reinforce', 'forget') NOT NULL,
                context TEXT COMMENT '访问上下文',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_memory (memory_type, memory_id),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='记忆访问日志'
        """)
        print("  ✅ 记忆访问日志表 (memory_access_log) 创建成功!")
        
        conn.commit()
        print("\n✅ 记忆数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 记忆数据库初始化失败: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    create_memory_database()
    init_memory_tables()
