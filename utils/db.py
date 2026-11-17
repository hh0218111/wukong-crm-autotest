"""数据库工具：造测试数据、校验落库结果、测后清理。

设计说明（面试可讲）：
- UI 创建一条线索再回查数据库，是"接口/页面/存储"三层一致的验证思路，
  和你排查590万回款bug时的分层定位法是同一套方法论
- 所有查询默认参数化（%s 占位符），不拼字符串，避免注入也避免转义坑
"""
from typing import Any

import pymysql

from config.settings import DB_CONFIG


def get_connection() -> pymysql.Connection:
    return pymysql.connect(**DB_CONFIG, autocommit=False)


def query(sql: str, params: tuple = ()) -> list[dict]:
    """只读查询，返回字典列表。"""
    conn = get_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """写操作（造数据/清理），返回影响行数。"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, params)
        conn.commit()
        return affected
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
