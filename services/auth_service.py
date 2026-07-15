"""
用户认证服务模块
处理用户登录、注册、密码加密等功能
"""

import hashlib
import sqlite3

import bcrypt

from data.config import get_accounts_db_config


class AuthService:
    """用户认证服务"""

    def __init__(self):
        """初始化认证服务"""
        self.db_config = get_accounts_db_config()
        self.db_path = self.db_config['database']

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def hash_password(self, password):
        """
        密码加密（bcrypt，cost=8 约 20ms，兼顾安全与性能）

        Args:
            password: 明文密码

        Returns:
            加密后的密码字符串（bcrypt 格式）
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=8)).decode('utf-8')

    def _verify_bcrypt(self, password, stored_password):
        """验证 bcrypt 格式的密码"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        except Exception:
            return False

    def _verify_legacy_sha256(self, password, stored_password):
        """验证旧版 SHA-256 格式的密码（向后兼容）"""
        try:
            if '$' not in stored_password:
                return False
            salt, pwd_hash = stored_password.split('$', 1)
            new_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return new_hash == pwd_hash
        except Exception:
            return False

    def verify_password(self, password, stored_password):
        """
        验证密码（优先 bcrypt，降级兼容 SHA-256）

        Args:
            password: 用户输入的明文密码
            stored_password: 数据库中存储的密码

        Returns:
            bool: 密码是否正确
        """
        if stored_password.startswith('$2b$') or stored_password.startswith('$2a$'):
            return self._verify_bcrypt(password, stored_password)
        return self._verify_legacy_sha256(password, stored_password)

    def _needs_rehash(self, stored_password):
        """检查是否需要重新哈希（旧版 SHA-256 → bcrypt）"""
        return not (stored_password.startswith('$2b$') or stored_password.startswith('$2a$'))

    def register_user(self, username, password, email=None, role='user'):
        """
        注册新用户

        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            role: 角色（默认student）

        Returns:
            dict: {'success': bool, 'message': str, 'user_id': int}
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return {'success': False, 'message': '用户名已存在'}

            # 加密密码
            hashed_password = self.hash_password(password)

            # 插入新用户
            cursor.execute(
                """INSERT INTO users (username, password, email, role, created_at, updated_at)
                   VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                (username, hashed_password, email, role)
            )
            conn.commit()

            user_id = cursor.lastrowid
            return {
                'success': True,
                'message': '注册成功',
                'user_id': user_id
            }

        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'message': f'注册失败：{e!s}'}
        finally:
            if conn:
                conn.close()

    def login_user(self, username, password):
        """
        用户登录

        Args:
            username: 用户名
            password: 密码

        Returns:
            dict: {'success': bool, 'message': str, 'user': dict}
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 查询用户
            cursor.execute(
                "SELECT id, username, password, email, role, created_at FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            user = dict(row) if row else None

            if not user:
                return {'success': False, 'message': '用户名或密码错误'}

            # 验证密码
            if not self.verify_password(password, user['password']):
                return {'success': False, 'message': '用户名或密码错误'}

            # 旧版 SHA-256 哈希自动迁移为 bcrypt
            if self._needs_rehash(user['password']):
                try:
                    new_hash = self.hash_password(password)
                    cursor.execute(
                        "UPDATE users SET password = ? WHERE id = ?",
                        (new_hash, user['id'])
                    )
                    conn.commit()
                except Exception:
                    pass  # 迁移失败不影响登录

            # 登录成功，移除密码字段
            user.pop('password', None)
            return {
                'success': True,
                'message': '登录成功',
                'user': user
            }

        except Exception as e:
            return {'success': False, 'message': f'登录失败：{e!s}'}
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id):
        """
        根据ID获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            dict: 用户信息（不包含密码）
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, username, email, role, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

        except Exception:
            return None
        finally:
            if conn:
                conn.close()

    def update_password(self, user_id, old_password, new_password):
        """
        修改密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            dict: {'success': bool, 'message': str}
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 获取当前密码
            cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            user = dict(row) if row else None

            if not user:
                return {'success': False, 'message': '用户不存在'}

            # 验证旧密码
            if not self.verify_password(old_password, user['password']):
                return {'success': False, 'message': '旧密码错误'}

            # 更新密码
            hashed_password = self.hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (hashed_password, user_id)
            )
            conn.commit()

            return {'success': True, 'message': '密码修改成功'}

        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'message': f'修改失败：{e!s}'}
        finally:
            if conn:
                conn.close()

    def get_all_users(self):
        """
        获取所有用户列表（管理员功能）

        Returns:
            list: 用户列表（不包含密码）
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC"
            )
            return [dict(row) for row in cursor.fetchall()]

        except Exception:
            return []
        finally:
            if conn:
                conn.close()

    def delete_user(self, user_id):
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            dict: {'success': bool, 'message': str}
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()

            if cursor.rowcount > 0:
                return {'success': True, 'message': '删除成功'}
            else:
                return {'success': False, 'message': '用户不存在'}

        except Exception as e:
            if conn:
                conn.rollback()
            return {'success': False, 'message': f'删除失败：{e!s}'}
        finally:
            if conn:
                conn.close()


# 创建全局认证服务实例
auth_service = AuthService()
