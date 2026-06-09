"""
多数据库架构初始化脚本
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
    
    conn = mysql.connector.connect(**temp_config, use_pure=True)
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
    conn = mysql.connector.connect(**config, use_pure=True)
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
    conn = mysql.connector.connect(**config, use_pure=True)
    cursor = conn.cursor()

    try:
        print("\n📦 初始化学生画像数据库 (ai_profiles)...")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                profile_data JSON NOT NULL COMMENT '学生画像数据',
                conversation_log JSON COMMENT '构建画像的对话记录',
                version INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生画像表'
        """)
        print("  ✅ 学生画像表 (student_profiles) 创建成功!")

        # 学期课程表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS course_schedules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                semester VARCHAR(20) NOT NULL COMMENT '学期标识，如 2026-春',
                courses JSON NOT NULL COMMENT '课程列表 [{name,day,start_time,end_time,location,teacher}]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_user_semester (user_id, semester),
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学期课程表'
        """)
        print("  ✅ 学期课程表 (course_schedules) 创建成功!")

        # 学习成绩表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_grades (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                semester VARCHAR(20) NOT NULL COMMENT '学期标识',
                course_name VARCHAR(100) NOT NULL COMMENT '课程名称',
                score DECIMAL(5,1) COMMENT '成绩',
                credits DECIMAL(3,1) COMMENT '学分',
                grade_type VARCHAR(20) DEFAULT 'exam' COMMENT '类型: exam/quiz/homework/overall',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_semester (user_id, semester),
                INDEX idx_user_course (user_id, course_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习成绩表'
        """)
        print("  ✅ 学习成绩表 (student_grades) 创建成功!")

        # 错题记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_notes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                subject VARCHAR(50) NOT NULL COMMENT '学科',
                chapter VARCHAR(100) COMMENT '章节',
                question TEXT NOT NULL COMMENT '题目内容',
                my_answer TEXT COMMENT '我的答案',
                correct_answer TEXT COMMENT '正确答案',
                error_reason TEXT COMMENT '错误原因分析',
                tags JSON COMMENT '标签 ["概念混淆","计算错误"]',
                mastery TINYINT DEFAULT 0 COMMENT '是否已掌握 0/1',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user (user_id),
                INDEX idx_subject (user_id, subject),
                INDEX idx_mastery (user_id, mastery)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题记录表'
        """)
        print("  ✅ 错题记录表 (error_notes) 创建成功!")

        # 学习计划表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS study_plans (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                semester VARCHAR(20) NOT NULL COMMENT '学期标识',
                plan_type VARCHAR(20) DEFAULT 'weekly' COMMENT 'weekly/exam/custom',
                plan_data JSON NOT NULL COMMENT '计划详情',
                status ENUM('active','completed','expired') DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_semester (user_id, semester),
                INDEX idx_status (user_id, status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习计划表'
        """)
        print("  ✅ 学习计划表 (study_plans) 创建成功!")

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
    conn = mysql.connector.connect(**config, use_pure=True)
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
    conn = mysql.connector.connect(**config, use_pure=True)
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
    conn = mysql.connector.connect(**config, use_pure=True)
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
    conn = mysql.connector.connect(**config, use_pure=True)
    cursor = conn.cursor()
    
    try:
        print("\n📦 初始化学习评估数据库 (ai_assessments)...")
        
        # 评估记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_assessments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                assessment_type ENUM('weekly', 'monthly', 'custom', 'comprehensive', 'auto_generated') NOT NULL,
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
    conn = mysql.connector.connect(**config, use_pure=True)
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
    """初始化RAG知识库数据库 — 与 data/rag_knowledge_base.py 保持一致"""
    config = get_rag_db_config()
    conn = mysql.connector.connect(**config, use_pure=True)
    cursor = conn.cursor()

    try:
        print("\n📦 初始化RAG知识库数据库 (ai_rag_knowledge)...")

        # 知识文档表 — 与 rag_knowledge_base.py 的 add_document() 对齐
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_documents (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文档 ID',
                title VARCHAR(500) NOT NULL COMMENT '文档标题',
                subject VARCHAR(50) NOT NULL COMMENT '所属学科',
                file_path VARCHAR(1000) COMMENT '文件存储路径',
                file_type VARCHAR(20) COMMENT '文件类型 (pdf/doc/ppt/txt)',
                file_size BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
                document_data JSON COMMENT '文档完整数据（JSON格式）',
                embedding JSON COMMENT '文档向量（Embedding）',
                embedding_model VARCHAR(100) DEFAULT 'spark-embedding' COMMENT '向量模型名称',
                uploaded_by VARCHAR(100) DEFAULT 'teacher' COMMENT '上传者',
                upload_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
                usage_count INT DEFAULT 0 COMMENT '使用次数',
                is_public TINYINT(1) DEFAULT 1 COMMENT '是否公开',
                FULLTEXT INDEX ft_title (title),
                INDEX idx_subject (subject),
                INDEX idx_upload_time (upload_time),
                INDEX idx_uploaded_by (uploaded_by),
                INDEX idx_usage_count (usage_count)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='知识文档表（JSON 格式）'
        """)
        print("  ✅ 知识文档表 (knowledge_documents) 创建成功!")

        # 知识点关联表 — 与 rag_knowledge_base.py 的 _add_knowledge_points() 对齐
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_points (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
                doc_id INT NOT NULL COMMENT '文档 ID',
                point_name VARCHAR(200) NOT NULL COMMENT '知识点名称',
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                UNIQUE KEY uk_doc_point (doc_id, point_name),
                INDEX idx_point_name (point_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='知识点关联表'
        """)
        print("  ✅ 知识点关联表 (knowledge_points) 创建成功!")

        # 文档分类表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_categories (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类 ID',
                category_name VARCHAR(100) NOT NULL COMMENT '分类名称',
                parent_id INT DEFAULT NULL COMMENT '父分类 ID',
                subject VARCHAR(50) COMMENT '所属学科',
                sort_order INT DEFAULT 0 COMMENT '排序顺序',
                FOREIGN KEY (parent_id) REFERENCES document_categories(id) ON DELETE SET NULL,
                UNIQUE KEY uk_category_name (category_name),
                INDEX idx_parent_id (parent_id),
                INDEX idx_subject (subject)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='文档分类表'
        """)
        print("  ✅ 文档分类表 (document_categories) 创建成功!")

        # 基础学科分类种子数据
        cursor.execute("""
            INSERT INTO document_categories (category_name, subject, sort_order)
            VALUES
            ('语文', '语文', 1), ('数学', '数学', 2), ('英语', '英语', 3),
            ('物理', '物理', 4), ('化学', '化学', 5), ('生物', '生物', 6),
            ('历史', '历史', 7), ('地理', '地理', 8), ('政治', '政治', 9),
            ('体育', '体育', 10), ('美术', '美术', 11), ('音乐', '音乐', 12),
            ('信息技术', '信息技术', 13)
            ON DUPLICATE KEY UPDATE subject = VALUES(subject)
        """)
        print("  ✅ 基础学科分类数据插入成功")

        # 文档分类关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_category_relation (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
                doc_id INT NOT NULL COMMENT '文档 ID',
                category_id INT NOT NULL COMMENT '分类 ID',
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE CASCADE,
                UNIQUE KEY uk_doc_category (doc_id, category_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='文档分类关联表'
        """)
        print("  ✅ 文档分类关联表 (document_category_relation) 创建成功!")

        # 使用日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_usage_log (
                id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志 ID',
                doc_id INT NOT NULL COMMENT '文档 ID',
                user_id INT COMMENT '用户 ID',
                action_type VARCHAR(50) COMMENT '操作类型 (view/download/search)',
                action_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
                search_keywords VARCHAR(500) COMMENT '搜索关键词',
                FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                INDEX idx_doc_id (doc_id),
                INDEX idx_user_id (user_id),
                INDEX idx_action_time (action_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            COMMENT='文档使用日志表'
        """)
        print("  ✅ 使用日志表 (document_usage_log) 创建成功!")

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
    print("多数据库架构初始化脚本")
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
