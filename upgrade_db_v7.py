"""
数据库架构升级脚本 - 支持多智能体学习系统
新增学生画像、学习资源、学习路径、行为追踪、效果评估等核心表
"""

import mysql.connector
from data.config import get_db_config

def upgrade_database():
    """升级数据库,添加新表结构"""
    
    # 获取配置
    DB_CONFIG = get_db_config()
    
    # 连接 MySQL
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    try:
        print("🔄 开始数据库架构升级...")
        
        # 1. 学生画像表 (支持对话式构建,≥6维度)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                profile_data JSON NOT NULL COMMENT '学生画像数据(JSON格式):
                    {
                        "knowledge_base": {...},      -- 知识基础
                        "cognitive_style": "...",     -- 认知风格(视觉/听觉/动觉)
                        "learning_goals": [...],      -- 学习目标
                        "weak_points": [...],         -- 易错点偏好
                        "learning_history": [...],    -- 学习历史
                        "interest_areas": [...],      -- 兴趣领域
                        "preferred_resources": [...], -- 资源偏好(视频/文档/实操)
                        "major": "...",               -- 专业
                        "grade_level": "...",         -- 年级
                        "update_time": "..."
                    }',
                conversation_log JSON COMMENT '构建画像的对话记录',
                version INT DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生画像表'
        """)
        print("✅ 学生画像表 (student_profiles) 创建成功!")
        
        # 2. 学习资源表 (支持5+种类型)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_resources (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                resource_type ENUM('document', 'mindmap', 'quiz', 'video', 'animation', 'code_case', 'reading') NOT NULL COMMENT '资源类型:文档/思维导图/题库/视频/动画/代码案例/拓展阅读',
                subject VARCHAR(50),
                difficulty_level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'intermediate',
                content_data JSON NOT NULL COMMENT '资源内容(JSON格式)',
                file_path VARCHAR(500) COMMENT '文件存储路径',
                thumbnail_path VARCHAR(500) COMMENT '缩略图路径',
                generated_by_agent VARCHAR(50) COMMENT '生成的智能体名称',
                target_profile JSON COMMENT '适用的学生画像特征',
                tags JSON COMMENT '标签列表',
                usage_count INT DEFAULT 0 COMMENT '使用次数',
                rating DECIMAL(3,2) DEFAULT 0 COMMENT '评分(0-5)',
                duration_minutes INT COMMENT '预计学习时长(分钟)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_type_subject (resource_type, subject),
                INDEX idx_difficulty (difficulty_level),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习资源表'
        """)
        print("✅ 学习资源表 (learning_resources) 创建成功!")
        
        # 3. 学习路径表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_paths (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                path_name VARCHAR(200) NOT NULL,
                description TEXT,
                path_data JSON NOT NULL COMMENT '学习路径数据(JSON格式):
                    {
                        "steps": [
                            {
                                "step_id": 1,
                                "title": "步骤标题",
                                "resource_id": 123,
                                "resource_type": "document",
                                "estimated_time": 30,
                                "prerequisites": [],
                                "next_steps": [2, 3],
                                "description": "步骤描述"
                            }
                        ],
                        "total_duration": 120,
                        "completion_rate": 0.45,
                        "current_step": 1
                    }',
                current_step INT DEFAULT 1,
                status ENUM('active', 'completed', 'paused', 'archived') DEFAULT 'active',
                total_steps INT DEFAULT 0,
                completed_steps INT DEFAULT 0,
                estimated_hours DECIMAL(5,2) COMMENT '预计总学时',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_status (user_id, status),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习路径表'
        """)
        print("✅ 学习路径表 (learning_paths) 创建成功!")
        
        # 4. 学习行为追踪表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_activities (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                resource_id INT,
                path_id INT,
                activity_type ENUM('view_resource', 'complete_resource', 'quiz_attempt', 'watch_video', 'run_code', 'read_document', 'create_mindmap') NOT NULL COMMENT '活动类型',
                duration_seconds INT DEFAULT 0 COMMENT '学习时长(秒)',
                score DECIMAL(5,2) COMMENT '得分(如有测验)',
                progress_percentage DECIMAL(5,2) DEFAULT 0 COMMENT '完成进度百分比',
                feedback JSON COMMENT '用户反馈',
                metadata JSON COMMENT '额外元数据',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (resource_id) REFERENCES learning_resources(id) ON DELETE SET NULL,
                FOREIGN KEY (path_id) REFERENCES learning_paths(id) ON DELETE SET NULL,
                INDEX idx_user_activity (user_id, activity_type),
                INDEX idx_resource (resource_id),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习行为追踪表'
        """)
        print("✅ 学习行为追踪表 (learning_activities) 创建成功!")
        
        # 5. 学习效果评估表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_assessments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                assessment_type ENUM('weekly', 'monthly', 'custom', 'auto_generated') NOT NULL COMMENT '评估类型',
                assessment_data JSON NOT NULL COMMENT '评估数据(JSON格式):
                    {
                        "knowledge_mastery": {          -- 知识点掌握度
                            "topic_1": 0.85,
                            "topic_2": 0.62
                        },
                        "skill_progress": {             -- 技能进步
                            "coding": {"before": 0.5, "after": 0.75},
                            "problem_solving": {"before": 0.6, "after": 0.8}
                        },
                        "engagement_level": 0.85,       -- 参与度
                        "time_investment": 45.5,        -- 投入时间(小时)
                        "strengths": ["快速理解概念"],   -- 优势
                        "weaknesses": ["实践应用不足"],  -- 不足
                        "recommendation": "建议加强...", -- 改进建议
                        "next_focus": ["动态规划"]       -- 下一步重点
                    }',
                period_start DATE COMMENT '评估周期开始',
                period_end DATE COMMENT '评估周期结束',
                overall_score DECIMAL(5,2) COMMENT '综合评分',
                improvement_suggestions JSON COMMENT '改进建议列表',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_period (user_id, period_start),
                INDEX idx_type (assessment_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习效果评估表'
        """)
        print("✅ 学习效果评估表 (learning_assessments) 创建成功!")
        
        # 6. 智能体协作日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_collaboration_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(100) NOT NULL COMMENT '会话ID',
                user_id INT,
                task_type VARCHAR(50) NOT NULL COMMENT '任务类型:generate_resource/build_profile/plan_path等',
                coordinator_input JSON COMMENT '协调智能体输入',
                agent_outputs JSON COMMENT '各智能体输出:
                    {
                        "profile_agent": {...},
                        "resource_agent": {...},
                        "path_agent": {...}
                    }',
                final_result JSON COMMENT '最终整合结果',
                execution_time_ms INT COMMENT '执行时间(毫秒)',
                status ENUM('success', 'failed', 'timeout') DEFAULT 'success',
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_session (session_id),
                INDEX idx_user_task (user_id, task_type),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体协作日志表'
        """)
        print("✅ 智能体协作日志表 (agent_collaboration_logs) 创建成功!")
        
        # 7. 为现有users表添加专业字段
        try:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS major VARCHAR(100) COMMENT '专业',
                ADD COLUMN IF NOT EXISTS grade_level VARCHAR(50) COMMENT '年级',
                ADD COLUMN IF NOT EXISTS learning_preferences JSON COMMENT '学习偏好'
            """)
            print("✅ 用户表 (users) 扩展字段添加成功!")
        except Exception as e:
            print(f"⚠️ 用户表扩展跳过(可能已存在): {str(e)}")
        
        conn.commit()
        print("\n🎉 数据库架构升级完成!所有新表创建成功!")
        print("\n📊 新增表统计:")
        print("  - student_profiles: 学生画像表(支持≥6维度)")
        print("  - learning_resources: 学习资源表(7种类型)")
        print("  - learning_paths: 学习路径表")
        print("  - learning_activities: 学习行为追踪表")
        print("  - learning_assessments: 学习效果评估表")
        print("  - agent_collaboration_logs: 智能体协作日志表")
        
    except Exception as e:
        print(f"\n❌ 数据库升级失败:{str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    upgrade_database()
