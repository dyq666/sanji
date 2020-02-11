__all__ = (
    'date_range',
)

import operator
from datetime import date, datetime, timedelta
from typing import Iterable, Union

from dateutil.relativedelta import relativedelta

Date = Union[date, datetime]


def date_range(start: Date,
               stop: Date,
               step: Union[relativedelta, timedelta] = timedelta(days=1),
               asc: bool = True) -> Iterable[Date]:
    """以 1 天为间隔迭代时间, 不包含 `end` (和内置的 `range` 函数保持一致)."""
    o = operator.lt if asc else operator.gt
    while o(start, stop):
        yield start
        start += step
