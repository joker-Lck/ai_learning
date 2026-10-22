"""
dbapi 兼容层 — 基于 PyMySQL。

业务代码里的 `import sqlite3` 可替换为 `from data import dbapi as db`，
继续使用 `?` 占位符、`row_factory = dbapi.Row`、`lastrowid`、PRAGMA 等旧接口。
"""

from __future__ import annotations

import os
import queue
import re
import threading
from pathlib import Path
from typing import Any

import pymysql
from pymysql import err as _pymysql_err
from pymysql.connections import Connection as _PyMySQLConnection
from pymysql.cursors import Cursor as _PyMySQLCursor

# ── 兼容 sqlite3 风格的异常别名 ──────────────────────────────
Error = _pymysql_err.Error
InterfaceError = _pymysql_err.InterfaceError
DatabaseError = _pymysql_err.DatabaseError
DataError = _pymysql_err.DataError
OperationalError = _pymysql_err.OperationalError
IntegrityError = _pymysql_err.IntegrityError
InternalError = _pymysql_err.InternalError
ProgrammingError = _pymysql_err.ProgrammingError
NotSupportedError = _pymysql_err.NotSupportedError

# 常量（兼容引用）
PARSE_DECLTYPES = 0
PARSE_COLNAMES = 0
threadsafety = 1
apilevel = "2.0"
paramstyle = "qmark"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass


_load_env()


def get_mysql_params() -> dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "123456"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
        "autocommit": False,
    }


# ═══════════════════════════════════════════
# 连接池（按库名复用底层 pymysql 连接）
# ═══════════════════════════════════════════

_POOL_MAX = int(os.getenv("MYSQL_POOL_SIZE", "8"))
_pools: dict[str, queue.Queue] = {}
_pools_lock = threading.Lock()


def _pool_for(db_name: str) -> queue.Queue:
    with _pools_lock:
        if db_name not in _pools:
            _pools[db_name] = queue.Queue(maxsize=_POOL_MAX)
        return _pools[db_name]


def _raw_connect(database: str | None) -> _PyMySQLConnection:
    """建立一条原始 pymysql 连接（含自动建库）"""
    params = get_mysql_params()
    last_err: Exception | None = None
    target = database
    for db in (target, None):
        try:
            conn = _PyMySQLConnection(
                host=params["host"],
                port=params["port"],
                user=params["user"],
                password=params["password"],
                database=db,
                charset=params["charset"],
                autocommit=bool(params.get("autocommit", False)),
            )
            if db is None and target:
                conn.cursor().execute(
                    f"CREATE DATABASE IF NOT EXISTS `{target}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                conn.commit()
                conn.database = target
            return conn
        except _pymysql_err.OperationalError as e:
            last_err = e
            if e.args and e.args[0] == 1049 and target:
                try:
                    bootstrap = _PyMySQLConnection(
                        host=params["host"],
                        port=params["port"],
                        user=params["user"],
                        password=params["password"],
                        charset=params["charset"],
                        autocommit=True,
                    )
                    bootstrap.cursor().execute(
                        f"CREATE DATABASE IF NOT EXISTS `{target}` "
                        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                    )
                    bootstrap.close()
                    continue
                except Exception as e2:
                    last_err = e2
            if db is not None:
                continue
    raise last_err or RuntimeError("MySQL 连接失败")


def _pool_acquire(database: str) -> _PyMySQLConnection:
    pool = _pool_for(database)
    try:
        conn = pool.get_nowait()
        # 探活：失效则丢弃重建
        try:
            conn.ping(reconnect=False)
            return conn
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return _raw_connect(database)
    except queue.Empty:
        return _raw_connect(database)


def _pool_release(database: str, conn: _PyMySQLConnection) -> None:
    if conn is None:
        return
    pool = _pool_for(database)
    try:
        conn.rollback()  # 还池前清理未提交事务
    except Exception:
        pass
    try:
        pool.put_nowait(conn)
    except queue.Full:
        # 池满则物理关闭
        try:
            conn.close()
        except Exception:
            pass


def close_all_pools() -> None:
    """测试/退出时清空连接池"""
    with _pools_lock:
        for pool in _pools.values():
            while True:
                try:
                    conn = pool.get_nowait()
                    conn.close()
                except Exception:
                    break
        _pools.clear()


def resolve_database(target: Any) -> str:
    """把历史「文件路径 / 配置 dict / 库名」统一解析成 MySQL 库名。"""
    if target is None:
        return os.getenv("MYSQL_DATABASE", "ai_auth")
    if isinstance(target, dict):
        target = target.get("database") or target.get("db") or target.get("name")
        if target is None:
            return os.getenv("MYSQL_DATABASE", "ai_auth")
    name = str(target).strip().replace("\\", "/")
    if "/" in name or name.endswith(".db"):
        name = Path(name).stem
    if name.endswith(".db"):
        name = name[: -len(".db")]
    return name


class Row:
    """模拟 dbapi.Row：支持下标、列名、keys()、dict()。"""

    __slots__ = ("_keys", "_vals")

    def __init__(self, keys: tuple[str, ...], vals: tuple[Any, ...]):
        self._keys = keys
        self._vals = vals

    def __getitem__(self, key: int | str) -> Any:
        if isinstance(key, int):
            return self._vals[key]
        try:
            return self._vals[self._keys.index(key)]
        except ValueError:
            raise IndexError(f"No item with that key: {key!r}") from None

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Row):
            return self._vals == other._vals
        return self._vals == other

    def __hash__(self) -> int:
        return hash(self._vals)

    def __iter__(self):
        return iter(self._vals)

    def __len__(self) -> int:
        return len(self._vals)

    def keys(self) -> tuple[str, ...]:
        return self._keys

    def __repr__(self) -> str:
        return f"<Row {dict(zip(self._keys, self._vals))!r}>"


class Cursor(_PyMySQLCursor):
    """支持 dbapi.Row / dict 行对象与 lastrowid。"""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._row_factory = None

    @property
    def row_factory(self):
        return self._row_factory

    @row_factory.setter
    def row_factory(self, value):
        self._row_factory = value

    def _convert_row(self, row: Any) -> Any:
        if row is None:
            return None
        if self._row_factory is None and not isinstance(self.connection, Connection):
            return row
        factory = getattr(self.connection, "row_factory", None) or self._row_factory
        if factory is None:
            return row
        if isinstance(row, dict):
            keys = tuple(row.keys())
            vals = tuple(row.values())
        else:
            description = self.description or ()
            keys = tuple(d[0] for d in description)
            vals = tuple(row)
        try:
            if factory is Row or getattr(factory, "__name__", "") == "Row":
                return Row(keys, vals)
            return factory(keys, vals)
        except TypeError:
            return Row(keys, vals)

    def fetchone(self):
        return self._convert_row(super().fetchone())

    def fetchmany(self, size: int | None = None):
        rows = super().fetchmany(size) if size is not None else super().fetchmany()
        return [self._convert_row(r) for r in rows]

    def fetchall(self):
        return [self._convert_row(r) for r in super().fetchall()]

    def __iter__(self):
        while True:
            row = self.fetchone()
            if row is None:
                break
            yield row


class DictCursor(_PyMySQLCursor):
    """pymysql 原生 DictCursor 兼容入口。"""

    pass


class Connection:
    """兼容 sqlite3.Connection 的常用接口。"""

    def __init__(self, database: str, **kwargs: Any):
        self._database = resolve_database(database)
        params = get_mysql_params()
        params.update(kwargs)
        params.setdefault("autocommit", False)
        self.row_factory = None
        self._conn = self._connect(params)
        self._cursor: Cursor | None = None

    def _connect(self, params: dict[str, Any]) -> _PyMySQLConnection:
        return _pool_acquire(self._database)

    # ── 兼容 API ──────────────────────────
    def cursor(self, factory: Any = None) -> Cursor:
        if factory is not None and factory is not Cursor:
            cur = self._conn.cursor()
            cur._row_factory = self.row_factory
            return cur
        cur = Cursor(self._conn)
        cur._row_factory = self.row_factory
        self._cursor = cur
        return cur

    def execute(self, sql: str, parameters: Any = ()) -> Cursor:
        cur = self.cursor()
        cur.execute(sql, parameters or ())
        return cur

    def executemany(self, sql: str, seq_of_parameters: Any) -> Cursor:
        cur = self.cursor()
        cur.executemany(sql, seq_of_parameters)
        return cur

    def executescript(self, sql_script: str) -> Cursor:
        cur = self.cursor()
        for statement in _split_sql(sql_script):
            if statement.strip():
                cur.execute(statement)
        return cur

    def commit(self) -> None:
        self._conn.commit()

    def rollback(self) -> None:
        self._conn.rollback()

    def close(self) -> None:
        """归还连接到池（而非物理关闭）"""
        try:
            if self._cursor is not None:
                self._cursor.close()
        except Exception:
            pass
        self._cursor = None
        try:
            _pool_release(self._database, self._conn)
        except Exception:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = None  # 防止重复归还

    def interrupt(self) -> None:
        pass

    @property
    def lastrowid(self) -> int | None:
        return self._conn.insert_id() if self._cursor is None else self._cursor.lastrowid

    @property
    def in_transaction(self) -> bool:
        return bool(getattr(self._conn, "get_autocommit", lambda: True)() is False)

    def create_function(self, *args: Any, **kwargs: Any) -> None:
        pass

    def create_aggregate(self, *args: Any, **kwargs: Any) -> None:
        pass

    def create_collation(self, *args: Any, **kwargs: Any) -> None:
        pass

    def set_trace_callback(self, *args: Any, **kwargs: Any) -> None:
        pass

    def backup(self, *args: Any, **kwargs: Any) -> None:
        raise NotSupportedError("MySQL 不支持 backup API")

    def __enter__(self) -> "Connection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()


_PLACEHOLDER_RE = re.compile(r"(?<!%)%s|\?")


def _split_sql(script: str) -> list[str]:
    """按分号切分 SQL（忽略字符串内的分号）。"""
    statements: list[str] = []
    buf: list[str] = []
    in_str = False
    quote = ""
    i = 0
    while i < len(script):
        ch = script[i]
        if in_str:
            buf.append(ch)
            if ch == quote:
                in_str = False
        elif ch in ("'", '"', "`"):
            in_str = True
            quote = ch
            buf.append(ch)
        elif ch == "-" and i + 1 < len(script) and script[i + 1] == "-":
            while i < len(script) and script[i] != "\n":
                i += 1
            continue
        elif ch == ";":
            statements.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    if "".join(buf).strip():
        statements.append("".join(buf))
    return statements


def _adapt_sql(sql: str) -> str:
    """把 sqlite3 风格 SQL 适配为 MySQL 可执行形式。"""
    out = sql
    # 占位符：优先保留已是 %s 的写法，把 ? 换成 %s
    out = out.replace("?", "%s")
    # 字符串内 %% 还原（避免被 pymysql 转义）
    # PRAGMA / sqlite_master 由调用方处理，这里只做通用替换
    out = re.sub(r"\bdatetime\(\s*'now'\s*(?:,\s*'localtime'\s*)?\)", "CURRENT_TIMESTAMP", out, flags=re.I)
    out = re.sub(r"\bdate\(\s*'now'\s*(?:,\s*'localtime'\s*)?\)", "CURRENT_DATE", out, flags=re.I)
    out = re.sub(r"\bstrftime\(\s*'%Y-%m-%d %H:%M:%S'\s*,\s*['\"]now['\"]\s*\)", "NOW()", out, flags=re.I)
    out = out.replace("INSERT OR REPLACE", "REPLACE")
    out = out.replace("INSERT OR IGNORE", "INSERT IGNORE")
    out = re.sub(r"\bjson_extract\s*\(", "JSON_EXTRACT(", out, flags=re.I)
    return out


class _CompatibleCursor(Cursor):
    def execute(self, query: Any, args: Any = None) -> "Cursor":
        if isinstance(query, str):
            q = query.strip()
            # PRAGMA → 无操作
            if q.upper().startswith("PRAGMA"):
                self._set_description_for_pragma()
                return self
            # sqlite_master 查询 → information_schema
            if "sqlite_master" in q.lower():
                self._execute_sqlite_master(q, args)
                return self
            query = _adapt_sql(q)
        super().execute(query, args)
        return self

    def executemany(self, query: Any, args: Any) -> "Cursor":
        if isinstance(query, str):
            query = _adapt_sql(query.strip())
        super().executemany(query, args)
        return self

    def _set_description_for_pragma(self) -> None:
        self.description = None
        self.rowcount = -1

    def _execute_sqlite_master(self, q: str, args: Any = None) -> int:
        """把 sqlite_master 元数据查询翻译到 information_schema。"""
        lower = q.lower()
        db = self.connection._database if hasattr(self.connection, "_database") else None
        if isinstance(self.connection, Connection):
            db = self.connection._database
        # 取表名
        name_match = re.search(r"name\s*=\s*['\"]([^'\"]+)['\"]", q, flags=re.I)
        table_name = name_match.group(1) if name_match else None
        type_match = re.search(r"type\s*=\s*['\"]([^'\"]+)['\"]", q, flags=re.I)
        obj_type = (type_match.group(1) if type_match else "table").lower()

        if "count(" in lower:
            sql = (
                "SELECT COUNT(*) AS cnt FROM information_schema.tables "
                "WHERE table_schema=%s AND table_type='BASE TABLE'"
            )
            params: list[Any] = [db]
            if table_name:
                sql += " AND table_name=%s"
                params.append(table_name)
            super().execute(sql, params)
            return

        sql = (
            "SELECT table_name AS name, 'table' AS type, NULL AS sql "
            "FROM information_schema.tables WHERE table_schema=%s AND table_type='BASE TABLE'"
        )
        params = [db]
        if table_name:
            sql += " AND table_name=%s"
            params.append(table_name)
        if obj_type in ("trigger", "view", "index"):
            # 无对应对象，返回空
            sql = "SELECT NULL AS name, NULL AS type, NULL AS sql FROM DUAL WHERE 1=0"
            params = []
        super().execute(sql, params)


# 覆盖 Connection.cursor 返回兼容 cursor
def _connection_cursor(self: Connection, factory: Any = None) -> _CompatibleCursor:
    cur = _CompatibleCursor(self._conn)
    cur._row_factory = self.row_factory
    self._cursor = cur
    return cur


Connection.cursor = _connection_cursor  # type: ignore[method-assign]


def connect(
    database: str = "ai_auth",
    timeout: float = 5.0,
    detect_types: int = 0,
    isolation_level: str | None = "",
    check_same_thread: bool = True,
    factory: Any = None,
    cached_statements: int = 0,
    uri: bool = False,
    **kwargs: Any,
) -> Connection:
    """dbapi.connect 兼容入口。"""
    kwargs.pop("timeout", None)
    return Connection(database, **kwargs)


# dbapi.Row 导出
__all__ = [
    "connect",
    "Connection",
    "Cursor",
    "DictCursor",
    "Row",
    "Error",
    "InterfaceError",
    "DatabaseError",
    "DataError",
    "OperationalError",
    "IntegrityError",
    "InternalError",
    "ProgrammingError",
    "NotSupportedError",
    "PARSE_COLNAMES",
    "PARSE_DECLTYPES",
    "apilevel",
    "paramstyle",
    "threadsafety",
    "get_mysql_params",
    "resolve_database",
]
