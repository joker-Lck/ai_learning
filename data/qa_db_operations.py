from core.logger import info, error, warning
"""AI 答疑专用数据库操作模块（JSON 格式存储）"""

import mysql.connector
from mysql.connector import pooling
import json
import time
from .config import get_qa_db_config
from datetime import datetime

# 查询缓存
_query_cache = {}
_CACHE_TTL = 300

def _get_cache_key(sql, params):
    """生成缓存键"""
    return f"{sql}:{str(params)}"

def _get_cached_result(cache_key):
    """获取缓存结果"""
    if cache_key in _query_cache:
        result, timestamp = _query_cache[cache_key]
        if time.time() - timestamp < _CACHE_TTL:
            return result
        else:
            del _query_cache[cache_key]
    return None

def _set_cache_result(cache_key, result):
    """设置缓存结果"""
    _query_cache[cache_key] = (result, time.time())
    # 限制缓存大小
    if len(_query_cache) > 100:
        oldest_key = min(_query_cache.keys(), key=lambda k: _query_cache[k][1])
        del _query_cache[oldest_key]

def _clear_search_cache():
    """清空搜索缓存"""
    keys_to_delete = [k for k in _query_cache.keys() if 'qa_records' in k or 'LIKE' in k]
    for key in keys_to_delete:
        del _query_cache[key]

class QADatabase:
    def __init__(self):
        self.conn_pool = None
        self._init_pool()
    
    def _init_pool(self):
        """初始化连接池"""
        try:
            config = get_qa_db_config()
            config['use_pure'] = True
            self.conn_pool = pooling.MySQLConnectionPool(
                pool_name="qa_pool",
                pool_size=5,
                pool_reset_session=True,
                **config
            )
        except Exception as e:
            error(f"连接池初始化失败：{str(e)}")
    
    def _get_connection(self):
        """从连接池获取连接"""
        if self.conn_pool:
            return self.conn_pool.get_connection()
        config = get_qa_db_config()
        config['use_pure'] = True
        return mysql.connector.connect(**config)
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = self._get_connection()
            self.cursor = self.conn.cursor(dictionary=True)
            return True
        except Exception as e:
            error(f"答疑数据库连接失败：{str(e)}")
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
            warning(f"关闭连接失败：{str(e)}")
    
    # ========== 用户相关操作 ==========
    def add_user(self, username, email, role='student'):
        """添加用户（同步到答疑数据库）"""
        try:
            self.connect()
            sql = "INSERT INTO users (username, email, role) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (username, email, role))
            self.conn.commit()
            return self.cursor.lastrowid
        except mysql.connector.errors.IntegrityError:
            # 用户已存在，获取用户信息
            return self.get_user_by_username(username)['id']
        except Exception as e:
            error(f"添加用户失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def get_user_by_username(self, username):
        """根据用户名获取用户"""
        try:
            self.connect()
            sql = "SELECT * FROM users WHERE username = %s"
            self.cursor.execute(sql, (username,))
            return self.cursor.fetchone()
        except Exception as e:
            error(f"获取用户失败：{str(e)}")
            return None
        finally:
            self.close()
    
    # ========== 问答记录相关操作（JSON 格式） ==========
    def add_qa_record(self, user_id, question_text, scenario, ai_response,
                      model_used='generalv3', tokens_used=None, response_time_ms=None):
        """添加问答记录（JSON 格式存储）"""
        try:
            self.connect()
            
            # 构建 JSON 数据
            question_data = {
                "text": question_text,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "scenario": scenario,
                "metadata": {
                    "source": "web",
                    "version": "1.0"
                }
            }
            
            ai_response_data = {
                "response": ai_response,
                "model": model_used,
                "tokens_used": tokens_used,
                "response_time_ms": response_time_ms,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            sql = """INSERT INTO qa_records 
                    (user_id, question_data, scenario, ai_response_data, model_used, tokens_used, response_time_ms) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            self.cursor.execute(sql, (
                user_id,
                json.dumps(question_data, ensure_ascii=False),
                scenario,
                json.dumps(ai_response_data, ensure_ascii=False),
                model_used,
                tokens_used,
                response_time_ms
            ))
            self.conn.commit()
            record_id = self.cursor.lastrowid
            
            # 添加记录后清空搜索缓存
            _clear_search_cache()
            
            return record_id
        except Exception as e:
            error(f"添加问答记录失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def get_qa_records_by_user(self, user_id, limit=100, scenario=None):
        """获取用户的问答记录（解析 JSON 数据）"""
        try:
            self.connect()
            if scenario:
                sql = """SELECT * FROM qa_records 
                        WHERE user_id = %s AND scenario = %s 
                        ORDER BY created_at DESC LIMIT %s"""
                self.cursor.execute(sql, (user_id, scenario, limit))
            else:
                sql = """SELECT * FROM qa_records 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC LIMIT %s"""
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
            error(f"获取问答记录失败：{str(e)}")
            return []
        finally:
            self.close()
    
    def get_qa_record_by_id(self, record_id):
        """根据 ID 获取问答记录"""
        try:
            self.connect()
            sql = "SELECT * FROM qa_records WHERE id = %s"
            self.cursor.execute(sql, (record_id,))
            return self.cursor.fetchone()
        except Exception as e:
            error(f"获取问答记录失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def search_similar_questions(self, question_text, limit=5):
        """搜索相似问题"""
        try:
            # 检查缓存
            cache_key = _get_cache_key("search_qa", question_text[:50])
            cached = _get_cached_result(cache_key)
            if cached:
                return cached
            
            self.connect()
            # 提取关键词（最多 3 个）
            keywords = [kw for kw in question_text.split() if len(kw) > 1][:3]
            
            if not keywords:
                return []
            
            # 查询必要字段
            like_conditions = []
            params = []
            for kw in keywords:
                like_conditions.append("question_text LIKE %s OR ai_response LIKE %s")
                params.extend([f"%{kw}%", f"%{kw}%"])
            
            like_sql = " OR ".join(like_conditions)
            sql = f"""SELECT id, question_text, ai_response, created_at
                     FROM qa_records
                     WHERE {like_sql}
                     ORDER BY created_at DESC
                     LIMIT %s"""
            
            all_params = params + [limit]
            self.cursor.execute(sql, all_params)
            results = self.cursor.fetchall()
            
            if not results:
                return []
            
            # 解析必要字段
            question_words = set(w.lower() for w in question_text.split() if len(w) > 1)
            enriched_results = []
            
            for result in results:
                # 计算相似度
                answer_words = set(w.lower() for w in (result['question_text'] + ' ' + result['ai_response']).split() if len(w) > 1)
                common_words = len(question_words & answer_words)
                total_words = len(question_words | answer_words)
                similarity = common_words / total_words if total_words > 0 else 0
                
                enriched_results.append({
                    'id': result['id'],
                    'question_text': result['question_text'],
                    'ai_response': result['ai_response'],
                    'similarity': similarity
                })
            
            # 按相似度排序
            enriched_results.sort(key=lambda x: x['similarity'], reverse=True)
            final_results = enriched_results[:limit]
            
            # 缓存结果
            if final_results:
                _set_cache_result(cache_key, final_results)
            
            return final_results
                
        except Exception as e:
            error(f"搜索相似问题失败：{str(e)}")
            return []
        finally:
            self.close()
    
    def update_feedback(self, record_id, rating, comment=None):
        """更新反馈"""
        try:
            self.connect()
            sql = "UPDATE qa_records SET feedback_rating = %s, feedback_comment = %s WHERE id = %s"
            self.cursor.execute(sql, (rating, comment, record_id))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"更新反馈失败：{str(e)}")
            return False
        finally:
            self.close()
    
    # ========== 会话相关操作 ==========
    def create_session(self, user_id, session_title=None, scenario=None):
        """创建新会话"""
        try:
            self.connect()
            sql = "INSERT INTO sessions (user_id, session_title, scenario) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (user_id, session_title, scenario))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            error(f"创建会话失败：{str(e)}")
            return None
        finally:
            self.close()
    
    def add_message_to_session(self, session_id, qa_record_id, message_order):
        """添加消息到会话"""
        try:
            self.connect()
            sql = "INSERT INTO session_messages (session_id, qa_record_id, message_order) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (session_id, qa_record_id, message_order))
            
            # 更新会话的消息数和最后活动时间
            sql = """UPDATE sessions 
                    SET message_count = message_count + 1, 
                        last_activity = CURRENT_TIMESTAMP 
                    WHERE id = %s"""
            self.cursor.execute(sql, (session_id,))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"添加消息到会话失败：{str(e)}")
            return False
        finally:
            self.close()
    
    def get_session_messages(self, session_id):
        """获取会话的所有消息"""
        try:
            self.connect()
            sql = """SELECT qr.* FROM qa_records qr
                    JOIN session_messages sm ON qr.id = sm.qa_record_id
                    WHERE sm.session_id = %s
                    ORDER BY sm.message_order ASC"""
            self.cursor.execute(sql, (session_id,))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"获取会话消息失败：{str(e)}")
            return []
        finally:
            self.close()
    
    def get_user_sessions(self, user_id, limit=50):
        """获取用户的会话列表"""
        try:
            self.connect()
            sql = """SELECT * FROM sessions 
                    WHERE user_id = %s 
                    ORDER BY last_activity DESC LIMIT %s"""
            self.cursor.execute(sql, (user_id, limit))
            return self.cursor.fetchall()
        except Exception as e:
            error(f"获取会话列表失败：{str(e)}")
            return []
        finally:
            self.close()
    
    # ========== 统计相关操作 ==========
    def update_user_statistics(self, user_id):
        """更新用户统计信息"""
        try:
            self.connect()
            
            # 计算统计数据
            stats_sql = """
                SELECT 
                    COUNT(*) as total_questions,
                    AVG(response_time_ms) as avg_response_time,
                    MAX(created_at) as last_question_time
                FROM qa_records
                WHERE user_id = %s
            """
            self.cursor.execute(stats_sql, (user_id,))
            stats = self.cursor.fetchone()
            
            # 获取最常用的场景
            scenario_sql = """
                SELECT scenario, COUNT(*) as cnt
                FROM qa_records
                WHERE user_id = %s
                GROUP BY scenario
                ORDER BY cnt DESC
                LIMIT 1
            """
            self.cursor.execute(scenario_sql, (user_id,))
            scenario_result = self.cursor.fetchone()
            most_used_scenario = scenario_result['scenario'] if scenario_result else None
            
            # 获取会话数
            session_sql = "SELECT COUNT(*) as total_sessions FROM sessions WHERE user_id = %s"
            self.cursor.execute(session_sql, (user_id,))
            session_result = self.cursor.fetchone()
            total_sessions = session_result['total_sessions']
            
            # 插入或更新统计
            upsert_sql = """
                INSERT INTO user_statistics 
                (user_id, total_questions, total_sessions, avg_response_time_ms, 
                 most_used_scenario, last_question_time)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                total_questions = VALUES(total_questions),
                total_sessions = VALUES(total_sessions),
                avg_response_time_ms = VALUES(avg_response_time_ms),
                most_used_scenario = VALUES(most_used_scenario),
                last_question_time = VALUES(last_question_time)
            """
            self.cursor.execute(upsert_sql, (
                user_id,
                stats['total_questions'],
                total_sessions,
                int(stats['avg_response_time']) if stats['avg_response_time'] else None,
                most_used_scenario,
                stats['last_question_time']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            error(f"更新统计信息失败：{str(e)}")
            return False
        finally:
            self.close()
    
    def get_user_statistics(self, user_id):
        """获取用户统计信息"""
        try:
            self.connect()
            sql = "SELECT * FROM user_statistics WHERE user_id = %s"
            self.cursor.execute(sql, (user_id,))
            return self.cursor.fetchone()
        except Exception as e:
            error(f"获取统计信息失败：{str(e)}")
            return None
        finally:
            self.close()

# 创建全局答疑数据库实例
qa_db = QADatabase()
