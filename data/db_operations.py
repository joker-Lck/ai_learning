"""
MySQL 数据库操作模块（JSON 格式存储）
提供数据库 CRUD 操作，所有复杂数据以 JSON 格式存储
"""

import mysql.connector
from mysql.connector import pooling
import json
from .config import get_db_config, get_auth_db_config, get_profile_db_config, get_resources_db_config, get_paths_db_config, get_assessments_db_config, get_agents_db_config
from datetime import datetime
from core.logger import db_operation_success, db_operation_failed, debug, error

class Database:
    def __init__(self, config_func=None):
        self.conn_pool = None
        self.conn = None
        self.cursor = None
        self._config_func = config_func or get_db_config
        self._init_pool()

    def _init_pool(self):
        """初始化连接池"""
        try:
            config = self._config_func()
            config['use_pure'] = True  # 绕过 C 扩展 Windows 兼容性问题
            pool_name = f"pool_{config.get('database', 'default')}"
            self.conn_pool = pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=5,
                pool_reset_session=True,
                **config
            )
        except Exception as e:
            error(f"连接池初始化失败：{str(e)}")

    def connect(self):
        """连接数据库"""
        try:
            if self.conn_pool:
                self.conn = self.conn_pool.get_connection()
            else:
                config = self._config_func()
                config['use_pure'] = True
                self.conn = mysql.connector.connect(**config)
            self.cursor = self.conn.cursor(dictionary=True)
            debug("数据库连接成功")
            return True
        except Exception as e:
            error(f"数据库连接失败：{str(e)}")
            db_operation_failed("connect", str(e))
            return False

    def close(self):
        """关闭连接"""
        try:
            if self.cursor:
                self.cursor.close()
                self.cursor = None
            if self.conn:
                self.conn.close()
                self.conn = None
        except Exception as e:
            error(f"关闭连接失败：{str(e)}")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    # ========== 用户相关操作 ==========
    def add_user(self, username, email, role='student'):
        """添加用户"""
        try:
            self.connect()
            sql = "INSERT INTO users (username, email, role) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (username, email, role))
            self.conn.commit()
            user_id = self.cursor.lastrowid
            db_operation_success("add_user", f"user_id={user_id}")
            return user_id
        except Exception as e:
            error(f"添加用户失败：{str(e)}")
            db_operation_failed("add_user", str(e))
            return None
        finally:
            self.close()
    
    def get_user(self, username):
        """获取用户信息"""
        try:
            self.connect()
            sql = "SELECT * FROM users WHERE username = %s"
            self.cursor.execute(sql, (username,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ 获取用户失败：{str(e)}")
            return None
        finally:
            self.close()
    
    # ========== 班级相关操作 ==========
    def add_class(self, class_name, teacher_id, grade_level):
        """添加班级"""
        try:
            self.connect()
            sql = "INSERT INTO classes (class_name, teacher_id, grade_level) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (class_name, teacher_id, grade_level))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"❌ 添加班级失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def get_class_by_name(self, class_name):
        """获取班级信息"""
        try:
            self.connect()
            sql = "SELECT * FROM classes WHERE class_name = %s"
            self.cursor.execute(sql, (class_name,))
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ 获取班级失败：{str(e)}")
            return None
        finally:
            self.close()
    
    # ========== 学生相关操作 ==========
    def add_student(self, class_id, student_name, student_no=None):
        """添加学生"""
        try:
            self.connect()
            sql = "INSERT INTO students (class_id, student_name, student_no) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (class_id, student_name, student_no))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"❌ 添加学生失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def get_students_by_class(self, class_id):
        """获取班级所有学生"""
        try:
            self.connect()
            sql = "SELECT * FROM students WHERE class_id = %s"
            self.cursor.execute(sql, (class_id,))
            return self.cursor.fetchall()
        except Exception as e:
            print(f"❌ 获取学生失败：{str(e)}")
            return []
        finally:
            self.close()
    
    # ========== 问题记录相关操作（JSON 格式） ==========
    def add_question(self, user_id, question_text, scenario, ai_response):
        """添加问题记录（JSON 格式存储）"""
        try:
            self.connect()
            
            # 构建 JSON 数据
            question_data = {
                "text": question_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "metadata": {
                    "source": "web",
                    "version": "1.0"
                }
            }
            
            ai_response_data = {
                "response": ai_response,
                "model": "generalv3",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            sql = "INSERT INTO questions (user_id, question_data, scenario, ai_response_data) VALUES (%s, %s, %s, %s)"
            self.cursor.execute(sql, (
                user_id, 
                json.dumps(question_data, ensure_ascii=False),
                scenario,
                json.dumps(ai_response_data, ensure_ascii=False)
            ))
            self.conn.commit()
            question_id = self.cursor.lastrowid
            db_operation_success("add_question", f"question_id={question_id}")
            return question_id
        except Exception as e:
            error(f"添加问题记录失败：{str(e)}")
            db_operation_failed("add_question", str(e))
            return None
        finally:
            self.close()
    
    def get_questions_by_user(self, user_id, limit=50):
        """获取用户的问题记录（解析 JSON 数据）"""
        try:
            self.connect()
            sql = "SELECT * FROM questions WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
            self.cursor.execute(sql, (user_id, limit))
            results = self.cursor.fetchall()
            
            # 解析 JSON 字段
            for record in results:
                if record.get('question_data'):
                    record['question_data'] = json.loads(record['question_data'])
                    # 兼容旧代码：提取 text 字段
                    record['question_text'] = record['question_data'].get('text', '')
                
                if record.get('ai_response_data'):
                    record['ai_response_data'] = json.loads(record['ai_response_data'])
                    # 兼容旧代码：提取 response 字段
                    record['ai_response'] = record['ai_response_data'].get('response', '')
            
            return results
        except Exception as e:
            error(f"获取问题记录失败：{str(e)}")
            db_operation_failed("get_questions_by_user", str(e))
            return []
        finally:
            self.close()
    
    # ========== 学情分析相关操作（JSON 格式） ==========
    def add_analysis(self, student_id, class_id, analysis_type, report_data, correct_rate=None, weak_points=None):
        """添加学情分析（JSON 格式存储）"""
        try:
            self.connect()
            
            # 构建 JSON 数据
            analysis_data = {
                "report": report_data,
                "correct_rate": correct_rate,
                "weak_points": weak_points if isinstance(weak_points, list) else [],
                "analysis_type": analysis_type,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0"
            }
            
            # weak_points 也存储为 JSON 数组
            weak_points_json = json.dumps(weak_points, ensure_ascii=False) if isinstance(weak_points, list) else None
            
            sql = "INSERT INTO learning_analysis (student_id, class_id, analysis_type, analysis_data, correct_rate, weak_points) VALUES (%s, %s, %s, %s, %s, %s)"
            self.cursor.execute(sql, (
                student_id, 
                class_id, 
                analysis_type,
                json.dumps(analysis_data, ensure_ascii=False),
                correct_rate,
                weak_points_json
            ))
            self.conn.commit()
            analysis_id = self.cursor.lastrowid
            db_operation_success("add_analysis", f"analysis_id={analysis_id}")
            return analysis_id
        except Exception as e:
            error(f"添加学情分析失败：{str(e)}")
            db_operation_failed("add_analysis", str(e))
            return None
        finally:
            self.close()
    
    def get_analysis_by_student(self, student_id):
        """获取学生的学情分析（解析 JSON 数据）"""
        try:
            self.connect()
            sql = "SELECT * FROM learning_analysis WHERE student_id = %s ORDER BY created_at DESC"
            self.cursor.execute(sql, (student_id,))
            results = self.cursor.fetchall()
            
            # 解析 JSON 字段
            for record in results:
                if record.get('analysis_data'):
                    record['analysis_data'] = json.loads(record['analysis_data'])
                    # 兼容旧代码：提取 report 字段
                    record['report_data'] = record['analysis_data'].get('report', '')
                
                if record.get('weak_points'):
                    record['weak_points'] = json.loads(record['weak_points'])
            
            return results
        except Exception as e:
            error(f"获取学情分析失败：{str(e)}")
            db_operation_failed("get_analysis_by_student", str(e))
            return []
        finally:
            self.close()

# 创建全局数据库实例
db = Database()  # 默认使用 auth 数据库

# 创建特定功能的数据库实例
profile_db = Database(config_func=get_profile_db_config)
resource_db = Database(config_func=get_resources_db_config)
path_db = Database(config_func=get_paths_db_config)
assessment_db = Database(config_func=get_assessments_db_config)
agent_db = Database(config_func=get_agents_db_config)
