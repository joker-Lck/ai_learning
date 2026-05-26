"""
MySQL 数据库初始化脚本
创建数据库和表结构
"""

import mysql.connector
from data.config import get_db_config

def init_database():
    """初始化数据库和表结构"""
    
    # 获取配置
    DB_CONFIG = get_db_config()
    
    # 连接 MySQL（不指定数据库）
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset='utf8mb4'
    )
    
    cursor = conn.cursor()
    
    try:
        # 创建数据库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {DB_CONFIG['database']}")
        
        print(f"✅ 数据库 '{DB_CONFIG['database']}' 创建成功！")
        
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL COMMENT '加密后的密码（salt$hash）',
                email VARCHAR(100),
                role ENUM('user', 'admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 用户表 (users) 创建成功！")
        
        # 创建班级表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_name VARCHAR(100) NOT NULL,
                teacher_id INT,
                grade_level VARCHAR(50),
                student_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 班级表 (classes) 创建成功！")
        
        # 创建学生名单表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT NOT NULL,
                student_name VARCHAR(50) NOT NULL,
                student_no VARCHAR(20),
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 学生名单表 (students) 创建成功！")
        
        # 创建问题记录表（JSON 格式存储）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                question_data JSON NOT NULL COMMENT '问题完整数据（JSON格式）',
                scenario VARCHAR(50),
                ai_response_data JSON COMMENT 'AI回复完整数据（JSON格式）',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_user_scenario (user_id, scenario),
                INDEX idx_created (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 问题记录表 (questions) 创建成功！（JSON 格式）")
        
        # 创建学情分析表（JSON 格式存储）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_analysis (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT,
                class_id INT,
                analysis_type VARCHAR(50),
                analysis_data JSON NOT NULL COMMENT '学情分析完整数据（JSON格式）',
                correct_rate DECIMAL(5,2),
                weak_points JSON COMMENT '薄弱知识点列表（JSON数组）',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                INDEX idx_student_type (student_id, analysis_type)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 学情分析表 (learning_analysis) 创建成功！（JSON 格式）")
        
        # 创建课件表（JSON 格式存储）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courseware (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                subject VARCHAR(50),
                grade_level VARCHAR(50),
                courseware_data JSON NOT NULL COMMENT '课件完整数据（JSON格式）',
                created_by INT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
                INDEX idx_subject_grade (subject, grade_level)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✅ 课件表 (courseware) 创建成功！（JSON 格式）")
        
        conn.commit()
        print("\n🎉 数据库初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败：{str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_database()
