"""
学生侧班级 API — 入班 / 我的班级 / 退出班级
"""

from fastapi import APIRouter, Depends

from backend.dependencies import require_auth
from backend.schemas.models import BaseResponse, ClassJoinRequest
from core.logger import error, info
from data.config import get_auth_db_path

from data import dbapi as sqlite3

router = APIRouter()


def _conn():
    c = sqlite3.connect(get_auth_db_path(), timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c


@router.post("/join-class", response_model=BaseResponse)
async def join_class(req: ClassJoinRequest, user: dict = Depends(require_auth)):
    """凭邀请码加入班级"""
    student_id = user["id"]
    code = req.invite_code.strip().upper()
    conn = _conn()
    try:
        cls = conn.execute(
            "SELECT id, name, is_open, max_students FROM classes WHERE invite_code=?",
            (code,)
        ).fetchone()
        if not cls:
            return BaseResponse(success=False, message="邀请码无效", error="邀请码无效")
        if not cls["is_open"]:
            return BaseResponse(success=False, message="该班级已关闭入班", error="已关闭入班")

        # 检查是否已在班
        existing = conn.execute(
            "SELECT id, status FROM class_students WHERE class_id=? AND student_id=?",
            (cls["id"], student_id)
        ).fetchone()
        if existing:
            if existing["status"] == "active":
                return BaseResponse(success=False, message="您已在该班级中", error="已加入")
            # 重新加入
            conn.execute(
                "UPDATE class_students SET status='active', joined_at=datetime('now','localtime') WHERE id=?",
                (existing["id"],)
            )
            conn.commit()
            info(f"学生 {student_id} 重新加入班级 {cls['id']}")
            return BaseResponse(success=True, message=f"已加入「{cls['name']}」", data={"class_id": cls["id"]})

        # 检查人数上限
        if cls["max_students"] is not None:
            cnt = conn.execute(
                "SELECT COUNT(*) c FROM class_students WHERE class_id=? AND status='active'",
                (cls["id"],)
            ).fetchone()["c"]
            if cnt >= cls["max_students"]:
                return BaseResponse(success=False, message="班级人数已满", error="人数已满")

        conn.execute(
            "INSERT INTO class_students (class_id, student_id) VALUES (?, ?)",
            (cls["id"], student_id)
        )
        conn.commit()
        info(f"学生 {student_id} 加入班级 {cls['id']} ({cls['name']})")
        return BaseResponse(
            success=True,
            message=f"已加入「{cls['name']}」",
            data={"class_id": cls["id"], "class_name": cls["name"]},
        )
    except Exception as e:
        conn.rollback()
        error(f"加入班级失败: {e}")
        return BaseResponse(success=False, message="加入班级失败", error=str(e))
    finally:
        conn.close()


@router.get("/my-classes", response_model=BaseResponse)
async def my_classes(user: dict = Depends(require_auth)):
    """我加入的班级列表"""
    student_id = user["id"]
    conn = _conn()
    try:
        cur = conn.execute("""
            SELECT c.id, c.name, c.subject, c.grade_level, c.semester,
                   c.description, cs.joined_at, cs.status,
                   u.username AS teacher_name
            FROM class_students cs
            JOIN classes c ON c.id = cs.class_id
            JOIN users u ON u.id = c.teacher_id
            WHERE cs.student_id = ? AND cs.status = 'active'
            ORDER BY cs.joined_at DESC
        """, (student_id,))
        classes = [dict(r) for r in cur.fetchall()]
        return BaseResponse(success=True, data=classes)
    except Exception as e:
        error(f"查询我的班级失败: {e}")
        return BaseResponse(success=False, message="查询失败", error=str(e))
    finally:
        conn.close()


@router.post("/leave-class/{class_id}", response_model=BaseResponse)
async def leave_class(class_id: int, user: dict = Depends(require_auth)):
    """退出班级"""
    student_id = user["id"]
    conn = _conn()
    try:
        cur = conn.execute(
            "UPDATE class_students SET status='left' WHERE class_id=? AND student_id=? AND status='active'",
            (class_id, student_id)
        )
        conn.commit()
        if cur.rowcount > 0:
            info(f"学生 {student_id} 退出班级 {class_id}")
            return BaseResponse(success=True, message="已退出班级")
        return BaseResponse(success=False, message="您不在该班级中", error="不在班级")
    except Exception as e:
        conn.rollback()
        error(f"退出班级失败: {e}")
        return BaseResponse(success=False, message="操作失败", error=str(e))
    finally:
        conn.close()
