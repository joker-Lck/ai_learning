"""
多数据库架构初始化脚本 v7.2
为每个核心功能创建独立数据库
"""

import mysql.connector
from data.config import (
    get_auth_db_config,
    get_profile_db_config,
    get_resources_db_config,
    get_paths_db_config,
    get_tutor_db_config,
    get_assessments_db_config,
    get_agents_db_config,
    get_rag_db_config
)

def create_database(config, db_name):
    """创建数据库"""
    # 连接 MySQL（不指定数据库）
    temp_config = config.copy()
    temp_config.pop('database', None)
    
    conn = mysql.connector.connect(**temp_config)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"✅ 数据库 '{db_name}' 创建成功!")
    finally:
        cursor.close()
        conn.close()

def init_auth_database():
    """初始化认证数据库"""
    config = get_auth_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化认证数据库 (ai_auth)...")
        
        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL COMMENT '加密后的密码',
                email VARCHAR(100),
                role ENUM('user', 'admin') DEFAULT 'user',
                major VARCHAR(100) COMMENT '专业',
                grade_level VARCHAR(50) COMMENT '年级',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("  ✅ 用户表 (users) 创建成功!")
        
        # 会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token VARCHAR(255) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_token (token),
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("  ✅ 会话表 (sessions) 创建成功!")
        
        conn.commit()
        print("✅ 认证数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 认证数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_profile_database():
    """初始化学生画像数据库"""
    config = get_profile_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化学生画像数据库 (ai_profiles)...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                profile_data JSON NOT NULL COMMENT '学生画像数据:
                    {
                        "knowledge_base": "...",
                        "cognitive_style": "...",
                        "learning_goals": "...",
                        "skill_level": "...",
                        "learning_preferences": [...],
                        "strengths": [...],
                        "weaknesses": [...],
                        "motivation": "..."
                    }',
                conversation_log JSON COMMENT '构建画像的对话记录',
                version INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生画像表'
        """)
        print("  ✅ 学生画像表 (student_profiles) 创建成功!")
        
        conn.commit()
        print("✅ 学生画像数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 学生画像数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_resources_database():
    """初始化学习资源数据库"""
    config = get_resources_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化学习资源数据库 (ai_resources)...")
        
        # 学习资源表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_resources (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                resource_type ENUM('document', 'mindmap', 'quiz', 'video', 'animation', 'code_case', 'reading') NOT NULL,
                subject VARCHAR(50),
                topic VARCHAR(100),
                difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
                content_data JSON NOT NULL COMMENT '资源内容',
                file_path VARCHAR(500),
                thumbnail_path VARCHAR(500),
                generated_by_agent VARCHAR(50),
                target_profile JSON COMMENT '适用的学生画像特征',
                tags JSON COMMENT '标签列表',
                usage_count INT DEFAULT 0,
                rating DECIMAL(3,2) DEFAULT 0,
                duration_minutes INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_type_subject (resource_type, subject),
                INDEX idx_difficulty (difficulty_level)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习资源表'
        """)
        print("  ✅ 学习资源表 (learning_resources) 创建成功!")
        
        # 资源安全检查日志
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resource_safety_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                resource_id INT,
                safety_check_result JSON NOT NULL COMMENT '安全检查结果',
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES learning_resources(id) ON DELETE CASCADE,
                INDEX idx_resource (resource_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='资源安全检查日志'
        """)
        print("  ✅ 资源安全检查日志表 (resource_safety_logs) 创建成功!")
        
        conn.commit()
        print("✅ 学习资源数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 学习资源数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_paths_database():
    """初始化学习路径数据库"""
    config = get_paths_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化学习路径数据库 (ai_paths)...")
        
        # 学习路径表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                path_name VARCHAR(200) NOT NULL,
                description TEXT,
                path_data JSON NOT NULL COMMENT '学习路径数据:
                    {
                        "goal": "...",
                        "total_steps": 5,
                        "estimated_duration": "10小时",
                        "steps": [...]
                    }',
                current_step INT DEFAULT 1,
                status ENUM('active', 'completed', 'paused', 'archived') DEFAULT 'active',
                total_steps INT DEFAULT 0,
                completed_steps INT DEFAULT 0,
                estimated_hours DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_status (user_id, status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习路径表'
        """)
        print("  ✅ 学习路径表 (learning_paths) 创建成功!")
        
        # 路径进度表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS path_progress (
                id INT AUTO_INCREMENT PRIMARY KEY,
                path_id INT NOT NULL,
                user_id INT NOT NULL,
                step_number INT NOT NULL,
                completed_at TIMESTAMP,
                time_spent INT COMMENT '花费时间(分钟)',
                FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE CASCADE,
                INDEX idx_path (path_id),
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路径进度表'
        """)
        print("  ✅ 路径进度表 (path_progress) 创建成功!")
        
        conn.commit()
        print("✅ 学习路径数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 学习路径数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_tutor_database():
    """初始化智能辅导数据库"""
    config = get_tutor_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化智能辅导数据库 (ai_tutor)...")
        
        # 辅导会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tutor_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                subject VARCHAR(50),
                session_name VARCHAR(200),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='辅导会话表'
        """)
        print("  ✅ 辅导会话表 (tutor_sessions) 创建成功!")
        
        # 辅导消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tutor_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id INT NOT NULL,
                role ENUM('user', 'assistant') NOT NULL,
                content TEXT NOT NULL,
                diagram TEXT COMMENT '图解内容',
                example TEXT COMMENT '示例内容',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES tutor_sessions(id) ON DELETE CASCADE,
                INDEX idx_session (session_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='辅导消息表'
        """)
        print("  ✅ 辅导消息表 (tutor_messages) 创建成功!")
        
        # 辅导知识引用表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tutor_knowledge_refs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                message_id INT NOT NULL,
                rag_source VARCHAR(500),
                confidence_score DECIMAL(3,2),
                FOREIGN KEY (message_id) REFERENCES tutor_messages(id) ON DELETE CASCADE,
                INDEX idx_message (message_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='辅导知识引用表'
        """)
        print("  ✅ 辅导知识引用表 (tutor_knowledge_refs) 创建成功!")
        
        conn.commit()
        print("✅ 智能辅导数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 智能辅导数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_assessments_database():
    """初始化学习评估数据库"""
    config = get_assessments_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化学习评估数据库 (ai_assessments)...")
        
        # 评估记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_assessments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                assessment_type ENUM('weekly', 'monthly', 'custom', 'auto_generated') NOT NULL,
                assessment_data JSON NOT NULL COMMENT '评估数据:
                    {
                        "overall_score": 85,
                        "dimensions": [...],
                        "strengths": [...],
                        "improvements": [...],
                        "recommendations": [...]
                    }',
                period_start DATE,
                period_end DATE,
                overall_score DECIMAL(5,2),
                improvement_suggestions JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_type (assessment_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习评估表'
        """)
        print("  ✅ 学习评估表 (learning_assessments) 创建成功!")
        
        # 评估维度表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessment_dimensions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                assessment_id INT NOT NULL,
                dimension_name VARCHAR(100) NOT NULL,
                score DECIMAL(5,2) NOT NULL,
                max_score DECIMAL(5,2) NOT NULL,
                level VARCHAR(50),
                feedback TEXT,
                FOREIGN KEY (assessment_id) REFERENCES learning_assessments(id) ON DELETE CASCADE,
                INDEX idx_assessment (assessment_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='评估维度表'
        """)
        print("  ✅ 评估维度表 (assessment_dimensions) 创建成功!")

        # 学习活动记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_activities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                activity_type VARCHAR(50) NOT NULL COMMENT '活动类型: tutor_query, resource_view, quiz_submit 等',
                metadata JSON COMMENT '活动元数据',
                duration_seconds INT DEFAULT 0 COMMENT '活动时长(秒)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_type (activity_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习活动记录表'
        """)
        print("  ✅ 学习活动记录表 (learning_activities) 创建成功!")

        conn.commit()
        print("✅ 学习评估数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 学习评估数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_agents_database():
    """初始化智能体协作数据库"""
    config = get_agents_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n 初始化智能体协作数据库 (ai_agents)...")
        
        # 智能体协作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_collaboration_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(100) NOT NULL,
                user_id INT,
                task_type VARCHAR(50) NOT NULL COMMENT '任务类型',
                coordinator_input JSON,
                agent_outputs JSON COMMENT '各智能体输出',
                final_result JSON,
                execution_time_ms INT,
                status ENUM('success', 'failed', 'timeout') DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session (session_id),
                INDEX idx_user_task (user_id, task_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体协作日志表'
        """)
        print("  ✅ 智能体协作日志表 (agent_collaboration_logs) 创建成功!")
        
        # 智能体任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                task_type VARCHAR(50) NOT NULL,
                assigned_agent VARCHAR(50),
                input_data JSON,
                output_data JSON,
                status ENUM('pending', 'running', 'completed', 'failed') DEFAULT 'pending',
                progress INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_agent (assigned_agent)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体任务表'
        """)
        print("  ✅ 智能体任务表 (agent_tasks) 创建成功!")
        
        conn.commit()
        print("✅ 智能体协作数据库初始化完成!")
        
    except Exception as e:
        print(f"❌ 智能体协作数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def init_rag_database():
    """初始化RAG知识库数据库"""
    config = get_rag_db_config()
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化RAG知识库数据库 (ai_rag_knowledge)...")
        
        # 知识文档表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                subject VARCHAR(50),
                document_type VARCHAR(50),
                content TEXT,
                embedding_vector JSON COMMENT '向量嵌入',
                file_path VARCHAR(500),
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_subject (subject)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识文档表'
        """)
        print("  ✅ 知识文档表 (knowledge_documents) 创建成功!")
        
        # 知识分块表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                document_id INT NOT NULL,
                chunk_content TEXT NOT NULL,
                chunk_index INT NOT NULL,
                embedding_vector JSON COMMENT '向量嵌入',
                metadata JSON,
                FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                INDEX idx_document (document_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识分块表'
        """)
        print("  ✅ 知识分块表 (knowledge_chunks) 创建成功!")
        
        conn.commit()
        print("✅ RAG知识库数据库初始化完成!")
        
    except Exception as e:
        print(f" RAG知识库数据库初始化失败: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数: 初始化所有数据库"""
    print("=" * 60)
    print("多数据库架构初始化脚本 v7.2")
    print("=" * 60)
    
    # 创建所有数据库
    databases = [
        (get_auth_db_config(), 'ai_auth'),
        (get_profile_db_config(), 'ai_profiles'),
        (get_resources_db_config(), 'ai_resources'),
        (get_paths_db_config(), 'ai_paths'),
        (get_tutor_db_config(), 'ai_tutor'),
        (get_assessments_db_config(), 'ai_assessments'),
        (get_agents_db_config(), 'ai_agents'),
        (get_rag_db_config(), 'ai_rag_knowledge'),
    ]
    
    print("\n📊 创建数据库...")
    for config, db_name in databases:
        create_database(config, db_name)
    
    # 初始化每个数据库的表结构
    init_auth_database()
    init_profile_database()
    init_resources_database()
    init_paths_database()
    init_tutor_database()
    init_assessments_database()
    init_agents_database()
    init_rag_database()
    
    print("\n" + "=" * 60)
    print(" 所有数据库初始化完成!")
    print("=" * 60)
    print("\n数据库列表:")
    print("  1. ai_auth - 认证与用户管理")
    print("  2. ai_profiles - 学生画像")
    print("  3. ai_resources - 学习资源")
    print("  4. ai_paths - 学习路径")
    print("  5. ai_tutor - 智能辅导")
    print("  6. ai_assessments - 学习效果评估")
    print("  7. ai_agents - 智能体协作")
    print("  8. ai_rag_knowledge - RAG知识库")

if __name__ == "__main__":
    main()
