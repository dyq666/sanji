__all__ = (
    'count',
    'get_create_table_sql',
    'query2sql',
)

from typing import TYPE_CHECKING

from peewee import SQL, fn

if TYPE_CHECKING:
    from peewee import BaseQuery, Model, Function


def count() -> 'Function':
    """返回 COUNT(*) 语句."""
    return fn.count(SQL('*'))


def get_create_table_sql(model: 'Model') -> str:
    """返回创建 table 的 sql 语句.

    copy from https://github.com/dyq666/sanji.
    """
    query = model._schema._create_table()
    db = model._schema.database
    ctx = db.get_sql_context()
    sql, params = ctx.sql(query).query()
    params = tuple(f"'{p}'" for p in params)
    params = params[0] if len(params) == 1 else params
    return sql % params


def query2sql(query: 'BaseQuery') -> str:
    """将 `query` 对象转为 sql 字符串."""
    sql, params = query.sql()
    params = tuple(f"'{p}'" for p in params)
    params = params[0] if len(params) == 1 else params
    return sql % params
