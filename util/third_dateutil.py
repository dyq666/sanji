__all__ = (
    'date_range',
)

from datetime import date, datetime, timedelta
from typing import Iterable, Union

from dateutil.relativedelta import relativedelta

Date = Union[date, datetime]
TimeDelta = Union[relativedelta, timedelta]


def date_range(start: Date, stop: Date, step: TimeDelta = timedelta(days=1),
               asc: bool = True) -> Iterable[Date]:
    """以 1 天为间隔迭代时间, 不包含 `end` (和内置的 `range` 函数保持一致)."""
    if asc:
        while start < stop:
            yield start
            start += step
    else:
        while start > stop:
            yield start
            start += step
