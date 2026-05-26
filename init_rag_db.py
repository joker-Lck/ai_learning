"""
RAG 知识库数据库初始化脚本
创建知识文档存储表结构
"""

import mysql.connector
from data.config import get_rag_db_config

def init_rag_database():
    """初始化 RAG 知识库数据库"""
    try:
        # 获取配置
        DB_CONFIG = get_rag_db_config()
        
        # 连接 MySQL（不指定数据库）
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        print("📊 开始初始化 RAG 知识库数据库...")
        
        # 1. 创建数据库
        cursor.execute("CREATE DATABASE IF NOT EXISTS ai_rag_knowledge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ 数据库创建成功：ai_rag_knowledge")
        
        # 使用数据库
        cursor.execute("USE ai_rag_knowledge")
        
        # 2. 创建知识文档表（JSON 格式存储）
        create_docs_table = """
        CREATE TABLE IF NOT EXISTS knowledge_documents (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文档 ID',
            title VARCHAR(500) NOT NULL COMMENT '文档标题',
            subject VARCHAR(50) NOT NULL COMMENT '所属学科',
            file_path VARCHAR(1000) COMMENT '文件存储路径',
            file_type VARCHAR(20) COMMENT '文件类型 (pdf/doc/ppt/txt)',
            file_size BIGINT DEFAULT 0 COMMENT '文件大小（字节）',
            document_data JSON COMMENT '文档完整数据（JSON格式）',
            embedding JSON COMMENT '文档向量（Embedding）',
            embedding_model VARCHAR(100) DEFAULT 'kimi-embedding' COMMENT '向量模型名称',
            uploaded_by VARCHAR(100) DEFAULT 'teacher' COMMENT '上传者',
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
            usage_count INT DEFAULT 0 COMMENT '使用次数',
            is_public TINYINT(1) DEFAULT 1 COMMENT '是否公开',
            
            -- 全文索引（用于语义检索，基于 JSON 提取的文本）
            FULLTEXT INDEX ft_title (title),
            
            -- 普通索引
            INDEX idx_subject (subject),
            INDEX idx_upload_time (upload_time),
            INDEX idx_uploaded_by (uploaded_by),
            INDEX idx_usage_count (usage_count)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='知识文档表（JSON 格式）';
        """
        cursor.execute(create_docs_table)
        print("✅ 知识文档表创建成功：knowledge_documents（JSON 格式）")
        
        # 3. 创建知识点关联表
        create_points_table = """
        CREATE TABLE IF NOT EXISTS knowledge_points (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
            doc_id INT NOT NULL COMMENT '文档 ID',
            point_name VARCHAR(200) NOT NULL COMMENT '知识点名称',
            
            -- 外键约束
            FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
            
            -- 唯一索引（避免重复）
            UNIQUE KEY uk_doc_point (doc_id, point_name),
            
            -- 普通索引
            INDEX idx_point_name (point_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='知识点关联表';
        """
        cursor.execute(create_points_table)
        print("✅ 知识点关联表创建成功：knowledge_points")
        
        # 4. 创建文档分类表
        create_categories_table = """
        CREATE TABLE IF NOT EXISTS document_categories (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类 ID',
            category_name VARCHAR(100) NOT NULL COMMENT '分类名称',
            parent_id INT DEFAULT NULL COMMENT '父分类 ID',
            subject VARCHAR(50) COMMENT '所属学科',
            sort_order INT DEFAULT 0 COMMENT '排序顺序',
            
            -- 自引用外键
            FOREIGN KEY (parent_id) REFERENCES document_categories(id) ON DELETE SET NULL,
            
            -- 唯一索引
            UNIQUE KEY uk_category_name (category_name),
            
            -- 普通索引
            INDEX idx_parent_id (parent_id),
            INDEX idx_subject (subject)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='文档分类表';
        """
        cursor.execute(create_categories_table)
        print("✅ 文档分类表创建成功：document_categories")
        
        # 5. 插入基础学科分类数据
        insert_categories = """
        INSERT INTO document_categories (category_name, subject, sort_order) 
        VALUES 
        ('语文', '语文', 1),
        ('数学', '数学', 2),
        ('英语', '英语', 3),
        ('物理', '物理', 4),
        ('化学', '化学', 5),
        ('生物', '生物', 6),
        ('历史', '历史', 7),
        ('地理', '地理', 8),
        ('政治', '政治', 9),
        ('体育', '体育', 10),
        ('美术', '美术', 11),
        ('音乐', '音乐', 12),
        ('信息技术', '信息技术', 13)
        ON DUPLICATE KEY UPDATE subject = VALUES(subject);
        """
        cursor.execute(insert_categories)
        print("✅ 基础学科分类数据插入成功")
        
        # 6. 创建文档 - 分类关联表
        create_doc_category_table = """
        CREATE TABLE IF NOT EXISTS document_category_relation (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'ID',
            doc_id INT NOT NULL COMMENT '文档 ID',
            category_id INT NOT NULL COMMENT '分类 ID',
            
            -- 外键约束
            FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE CASCADE,
            
            -- 唯一索引
            UNIQUE KEY uk_doc_category (doc_id, category_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='文档分类关联表';
        """
        cursor.execute(create_doc_category_table)
        print("✅ 文档分类关联表创建成功")
        
        # 7. 创建使用日志表
        create_usage_log_table = """
        CREATE TABLE IF NOT EXISTS document_usage_log (
            id INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志 ID',
            doc_id INT NOT NULL COMMENT '文档 ID',
            user_id INT COMMENT '用户 ID',
            action_type VARCHAR(50) COMMENT '操作类型 (view/download/search)',
            action_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
            search_keywords VARCHAR(500) COMMENT '搜索关键词',
            
            -- 外键约束
            FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id) ON DELETE CASCADE,
            
            -- 普通索引
            INDEX idx_doc_id (doc_id),
            INDEX idx_user_id (user_id),
            INDEX idx_action_time (action_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
        COMMENT='文档使用日志表';
        """
        cursor.execute(create_usage_log_table)
        print("✅ 使用日志表创建成功")
        
        conn.commit()
        
        print("\n" + "="*50)
        print("🎉 RAG 知识库数据库初始化完成！")
        print("="*50)
        print("\n📊 数据库信息:")
        print("  - 数据库名：ai_rag_knowledge")
        print("  - 字符集：utf8mb4")
        print("  - 排序规则：utf8mb4_unicode_ci")
        print("\n📋 已创建的表:")
        print("  1. knowledge_documents - 知识文档表")
        print("  2. knowledge_points - 知识点关联表")
        print("  3. document_categories - 文档分类表")
        print("  4. document_category_relation - 文档分类关联表")
        print("  5. document_usage_log - 文档使用日志表")
        print("\n✨ 功能特性:")
        print("  ✅ 支持全文检索（FULLTEXT 索引）")
        print("  ✅ 支持多学科分类存储")
        print("  ✅ 支持知识点标签管理")
        print("  ✅ 支持使用统计和日志追踪")
        print("="*50)
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as err:
        print(f"\n❌ 数据库初始化失败：{err}")
        return False
    except Exception as e:
        print(f"\n❌ 未知错误：{str(e)}")
        return False

if __name__ == "__main__":
    # 运行初始化
    success = init_rag_database()
    
    if success:
        print("\n✅ RAG 知识库初始化成功！可以开始使用。")
    else:
        print("\n❌ RAG 知识库初始化失败，请检查错误信息。")
