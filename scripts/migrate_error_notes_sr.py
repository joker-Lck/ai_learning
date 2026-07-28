"""
数据库迁移：为 error_notes 表添加间隔重复字段
"""
import sqlite3
import os

def get_db_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'databases', 'ai_profiles.db')

def migrate():
    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(f"数据库不存在: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查是否已有新字段
    cursor.execute("PRAGMA table_info(error_notes)")
    columns = [row[1] for row in cursor.fetchall()]

    new_columns = {
        'review_count': 'INTEGER DEFAULT 0',
        'last_review': 'TIMESTAMP',
        'next_review': 'TIMESTAMP',
        'ease_factor': 'REAL DEFAULT 2.5',
        'review_interval': 'INTEGER DEFAULT 1',
    }

    added = 0
    for col_name, col_def in new_columns.items():
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE error_notes ADD COLUMN {col_name} {col_def}")
            added += 1
            print(f"  + 添加字段: {col_name}")

    # 为已存在的错题设置 next_review = created_at + 1天（立即进入复习调度）
    if added > 0:
        cursor.execute("""
            UPDATE error_notes
            SET next_review = datetime(created_at, '+1 day'),
                review_count = 0,
                ease_factor = 2.5,
                review_interval = 1
            WHERE next_review IS NULL
        """)
        updated = cursor.rowcount
        print(f"  + 初始化 {updated} 条错题的复习调度")

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_next_review ON error_notes(user_id, next_review)")

    conn.commit()
    conn.close()
    print(f"[OK] error_notes 间隔重复字段迁移完成 (新增 {added} 个字段)")

if __name__ == '__main__':
    migrate()
