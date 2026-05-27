"""
AI 答疑专用数据库初始化脚本
"""

import mysql.connector
from data.config import get_qa_db_config

def init_qa_database():
    """初始化 AI 答疑专用数据库"""
    
    # 获取配置
    QA_DB_CONFIG = get_qa_db_config()
    
    # 连接 MySQL（不指定数据库）
    conn = mysql.connector.connect(
        host=QA_DB_CONFIG['host'],
        port=QA_DB_CONFIG['port'],
        user=QA_DB_CONFIG['user'],
        password=QA_DB_CONFIG['password'],
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    try:
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {QA_DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {QA_DB_CONFIG['database']}")
        
        print(f"✅ 数据库 '{QA_DB_CONFIG['database']}' 创建成功！")
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100),
                role ENUM('user', 'admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 用户表 (users) 创建成功！")
        
        # 创建问答记录表（核心表，JSON 格式存储）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS qa_records (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                question_data JSON NOT NULL COMMENT '问题完整数据（JSON格式）',
                scenario VARCHAR(100),
                ai_response_data JSON COMMENT 'AI回复完整数据（JSON格式）',
                model_used VARCHAR(50) DEFAULT 'generalv3',
                tokens_used INT,
                response_time_ms INT,
                feedback_rating TINYINT,
                feedback_comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_user_created (user_id, created_at),
                INDEX idx_scenario (scenario),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 问答记录表 (qa_records) 创建成功！（JSON 格式）")
        
        # 创建会话表（用于组织多轮对话）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_title VARCHAR(200),
                scenario VARCHAR(100),
                message_count INT DEFAULT 0,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_session (user_id, last_activity)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 会话表 (sessions) 创建成功！")
        
        # 创建会话消息关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_messages (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                session_id BIGINT NOT NULL,
                qa_record_id BIGINT NOT NULL,
                message_order INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (qa_record_id) REFERENCES qa_records(id) ON DELETE CASCADE,
                INDEX idx_session_order (session_id, message_order)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 会话消息关联表 (session_messages) 创建成功！")
        
        # 创建统计汇总表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT UNIQUE NOT NULL,
                total_questions INT DEFAULT 0,
                total_sessions INT DEFAULT 0,
                avg_response_time_ms INT,
                most_used_scenario VARCHAR(100),
                last_question_time TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 统计汇总表 (user_statistics) 创建成功！")
        
        conn.commit()
        print("\n🎉 AI 答疑专用数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败：{str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_qa_database()
