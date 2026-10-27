"""
老师端 API 测试 — 班级管理 + 学情代查 + 权限校验
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ==================== ClassService 测试 ====================

class TestClassService:
    """ClassService 单元测试"""

    def _get_service(self):
        from services.class_service import ClassService
        return ClassService()

    def _get_auth_service(self):
        from services.auth_service import AuthService
        return AuthService()

    @pytest.fixture(autouse=True)
    def setup(self):
        self.cs = self._get_service()
        self.auth = self._get_auth_service()
        # 创建测试用户
        r1 = self.auth.register_user('t_test_teacher', 'test123', role='teacher')
        self.teacher_id = r1['user_id']
        r2 = self.auth.register_user('t_test_student', 'test123', role='student')
        self.student_id = r2['user_id']
        yield
        # 清理
        from data import dbapi as dbapi
        from data.config import get_auth_db_path
        conn = dbapi.connect(get_auth_db_path())
        conn.execute("DELETE FROM class_students WHERE student_id=?", (self.student_id,))
        conn.execute("DELETE FROM classes WHERE teacher_id=?", (self.teacher_id,))
        conn.execute("DELETE FROM users WHERE id IN (?, ?)", (self.teacher_id, self.student_id))
        conn.commit()
        conn.close()

    def test_create_class(self):
        result = self.cs.create_class(
            self.teacher_id, '测试班级', subject='数学', max_students=5
        )
        assert result['success'] is True
        assert 'class_id' in result
        assert 'invite_code' in result
        assert len(result['invite_code']) == 6

    def test_list_classes(self):
        self.cs.create_class(self.teacher_id, '班级A')
        self.cs.create_class(self.teacher_id, '班级B')
        classes = self.cs.list_classes(self.teacher_id)
        assert len(classes) >= 2

    def test_get_class(self):
        r = self.cs.create_class(self.teacher_id, '详情测试')
        cls = self.cs.get_class(r['class_id'], teacher_id=self.teacher_id)
        assert cls is not None
        assert cls['name'] == '详情测试'

    def test_update_class(self):
        r = self.cs.create_class(self.teacher_id, '旧名')
        result = self.cs.update_class(r['class_id'], self.teacher_id, name='新名')
        assert result['success'] is True
        cls = self.cs.get_class(r['class_id'], teacher_id=self.teacher_id)
        assert cls['name'] == '新名'

    def test_reset_invite_code(self):
        r = self.cs.create_class(self.teacher_id, '重置测试')
        old_code = r['invite_code']
        result = self.cs.reset_invite_code(r['class_id'], self.teacher_id)
        assert result['success'] is True
        assert result['invite_code'] != old_code

    def test_set_class_open(self):
        r = self.cs.create_class(self.teacher_id, '开关测试')
        result = self.cs.set_class_open(r['class_id'], self.teacher_id, is_open=False)
        assert result['success'] is True
        cls = self.cs.get_class(r['class_id'], teacher_id=self.teacher_id)
        assert cls['is_open'] == 0

    def test_assert_student_in_class(self):
        r = self.cs.create_class(self.teacher_id, '关系测试')
        class_id = r['class_id']
        # 未加入时应返回 False
        assert self.cs.assert_student_in_teacher_class(self.teacher_id, self.student_id) is False
        # 手动加入
        from data import dbapi as dbapi
        from data.config import get_auth_db_path
        conn = dbapi.connect(get_auth_db_path())
        conn.execute(
            "INSERT INTO class_students (class_id, student_id) VALUES (?, ?)",
            (class_id, self.student_id)
        )
        conn.commit()
        conn.close()
        # 加入后应返回 True
        assert self.cs.assert_student_in_teacher_class(self.teacher_id, self.student_id) is True

    def test_remove_student(self):
        r = self.cs.create_class(self.teacher_id, '移除测试')
        class_id = r['class_id']
        from data import dbapi as dbapi
        from data.config import get_auth_db_path
        conn = dbapi.connect(get_auth_db_path())
        conn.execute(
            "INSERT INTO class_students (class_id, student_id) VALUES (?, ?)",
            (class_id, self.student_id)
        )
        conn.commit()
        conn.close()
        result = self.cs.remove_student(class_id, self.student_id, self.teacher_id)
        assert result['success'] is True

    def test_list_all_students(self):
        r = self.cs.create_class(self.teacher_id, '全部学生测试')
        class_id = r['class_id']
        from data import dbapi as dbapi
        from data.config import get_auth_db_path
        conn = dbapi.connect(get_auth_db_path())
        conn.execute(
            "INSERT INTO class_students (class_id, student_id) VALUES (?, ?)",
            (class_id, self.student_id)
        )
        conn.commit()
        conn.close()
        students = self.cs.list_all_students(self.teacher_id)
        assert len(students) >= 1
        assert students[0]['username'] == 't_test_student'


# ==================== StudentMonitorService 测试 ====================

class TestStudentMonitorService:

    def test_get_student_brief(self):
        from services.class_service import StudentMonitorService
        sms = StudentMonitorService()
        brief = sms.get_student_brief(1)  # user_id=1 should exist
        assert 'user_id' in brief

    def test_get_profile_empty(self):
        from services.class_service import StudentMonitorService
        sms = StudentMonitorService()
        profile = sms.get_profile(99999)  # nonexistent
        assert profile == {}

    def test_get_course_schedule_empty(self):
        from services.class_service import StudentMonitorService
        sms = StudentMonitorService()
        schedule = sms.get_course_schedule(99999)
        assert schedule == []

    def test_get_grades_empty(self):
        from services.class_service import StudentMonitorService
        sms = StudentMonitorService()
        grades = sms.get_grades(99999)
        assert grades == []


# ==================== 角色迁移验证 ====================

class TestRoleMigration:

    def test_no_legacy_user_roles(self):
        from data import dbapi as dbapi
        from data.config import get_auth_db_path
        conn = dbapi.connect(get_auth_db_path())
        count = conn.execute(
            "SELECT COUNT(*) FROM users WHERE role = 'user'"
        ).fetchone()[0]
        conn.close()
        assert count == 0, f"仍有 {count} 个存量 role='user' 未迁移"

    def test_classes_tables_exist(self):
        from data import dbapi as dbapi
        from data.config import get_auth_db_path
        conn = dbapi.connect(get_auth_db_path())
        db_name = get_auth_db_path()
        try:
            rows = conn.execute(
                "SELECT TABLE_NAME FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = ? AND TABLE_NAME IN ('classes', 'class_students')",
                (db_name,),
            ).fetchall()
            tables = [r[0] for r in rows]
        except Exception:
            tables = [
                r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('classes', 'class_students')"
                ).fetchall()
            ]
        conn.close()
        assert 'classes' in tables
        assert 'class_students' in tables

    def test_role_check_allows_teacher_student(self):
        # 角色合法性由 RBAC 层保证（MySQL 8.0.12 不 enforce CHECK，迁移后无 CHECK 约束）
        from backend.dependencies import ROLE_HIERARCHY
        assert ROLE_HIERARCHY.get("teacher", 0) > 0
        assert ROLE_HIERARCHY.get("student", 0) > 0
        from data import dbapi as dbapi
        from data.config import get_auth_db_path
        conn = dbapi.connect(get_auth_db_path())
        try:
            rows = conn.execute(
                "SELECT COLUMN_DEFAULT FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = 'users' AND COLUMN_NAME = 'role'",
                (get_auth_db_path(),),
            ).fetchall()
            default = rows[0][0] if rows else None
        except Exception:
            row = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name='users'"
            ).fetchone()
            default = row[0] if row else ""
        conn.close()
        assert default is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
