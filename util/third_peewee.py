__all__ = (
    'get_create_query',
    'query2sql',
)

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from peewee import Model, ModelSelect, Database


def get_create_query(model: 'Model') -> 'ModelSelect':
    """返回创建 model 的 `query` 对象."""
    return model._schema._create_table()


def query2sql(query: 'ModelSelect', db: 'Database') -> str:
    """将 `query` 对象转为 sql 字符串."""
    ctx = db.get_sql_context()
    sql, params = ctx.sql(query).query()
    params = tuple(f"'{p}'" for p in params)
    params = params[0] if len(params) == 1 else params
    return sql % params