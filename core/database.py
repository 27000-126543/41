"""
数据库模块 - SQLite数据库连接与初始化
"""
import sqlite3
import threading
from contextlib import contextmanager
from config.settings import DATABASE_PATH

_local = threading.local()


def get_connection():
    if not hasattr(_local, 'conn'):
        _local.conn = sqlite3.connect(DATABASE_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA foreign_keys = ON")
    return _local.conn


@contextmanager
def get_cursor():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def close_connection():
    if hasattr(_local, 'conn'):
        _local.conn.close()
        delattr(_local, 'conn')
