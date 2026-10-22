"""
一次性迁移脚本：角色统一 + 班级表
1. 备份 auth DB
2. 重建 users 表（放宽 role CHECK 为 user/admin/guest/teacher/student）
3. 创建 classes / class_students 表
4. 将存量 role='user' 升级为 'student'
"""

import shutil
from data import dbapi as sqlite3
import sys
from datetime import datetime
from pathlib import Path

# 项目根目录
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.config import get_auth_db_path  # noqa: E402


def migrate():
    db_path = get_auth_db_path()
    print(f"[MIGRATE] 目标数据库: {db_path}")

    # ── 1. 备份 ──
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.bak_{ts}"
    shutil.copy2(db_path, backup_path)
    print(f"[MIGRATE] 备份完成 → {backup_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=OFF")  # 重建表时临时关闭

    try:
        # ── 2. 重建 users 表（SQLite 不支持 ALTER CHECK） ──
        print("[MIGRATE] 重建 users 表（放宽 role CHECK）...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                role TEXT CHECK(role IN ('user', 'admin', 'guest', 'teacher', 'student')) DEFAULT 'student',
                major TEXT,
                grade_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            INSERT INTO users_new (id, username, password, email, role, major, grade_level, created_at, updated_at)
            SELECT id, username, password, email, role, major, grade_level, created_at, updated_at
            FROM users;

            DROP TABLE users;
            ALTER TABLE users_new RENAME TO users;

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        """)

        # 恢复 updated_at 触发器
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS trg_users_updated_at
            AFTER UPDATE ON users
            FOR EACH ROW
            BEGIN
                UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END
        """)

        # ── 3. 创建 classes / class_students ──
        print("[MIGRATE] 创建 classes / class_students 表...")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                teacher_id INTEGER NOT NULL,
                subject TEXT DEFAULT '',
                grade_level TEXT DEFAULT '',
                semester TEXT DEFAULT '',
                invite_code TEXT NOT NULL UNIQUE,
                is_open INTEGER DEFAULT 1,
                max_students INTEGER DEFAULT NULL,
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime')),
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_classes_teacher ON classes(teacher_id);

            CREATE TRIGGER IF NOT EXISTS trg_classes_updated_at
            AFTER UPDATE ON classes
            FOR EACH ROW
            BEGIN
                UPDATE classes SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;

            CREATE TABLE IF NOT EXISTS class_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                joined_at TEXT DEFAULT (datetime('now','localtime')),
                status TEXT DEFAULT 'active',
                UNIQUE(class_id, student_id),
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_cs_class ON class_students(class_id);
            CREATE INDEX IF NOT EXISTS idx_cs_student ON class_students(student_id);
        """)

        # ── 4. 存量 role='user' → 'student' ──
        print("[MIGRATE] 将存量 role='user' 升级为 'student'...")
        cursor = conn.execute("UPDATE users SET role = 'student' WHERE role = 'user'")
        migrated = cursor.rowcount
        print(f"[MIGRATE] 已升级 {migrated} 个用户")

        conn.commit()
        print("[MIGRATE] 迁移完成 ✓")

        # ── 验证 ──
        conn.execute("PRAGMA foreign_keys=ON")
        rows = conn.execute("SELECT role, COUNT(*) FROM users GROUP BY role").fetchall()
        print("\n[VERIFY] 当前角色分布:")
        for role, cnt in rows:
            print(f"  {role}: {cnt}")

        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('classes','class_students')"
        ).fetchall()
        print(f"[VERIFY] 新表: {[t[0] for t in tables]}")

    except Exception as e:
        conn.rollback()
        print(f"[MIGRATE] 迁移失败: {e}")
        print(f"[MIGRATE] 可从备份恢复: {backup_path}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
