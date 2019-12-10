__all__ = (
    'query_2_sql',
)

from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from peewee import ModelSelect, Database


def query_2_sql(query: 'ModelSelect', db: 'Database') -> Tuple[str, str]:
    """将 query 对象转为 sql 字符串."""
    ctx = db.get_sql_context()
    sql, params = ctx.sql(query).query()
    return sql, params
