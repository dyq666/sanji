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
    """时间迭代器.

    参数的命名和功能都与内置的 `range` 保持一致.
    比较特殊的是增加了一个参数 `asc`, 用于标记是否为递增时间序列.
    """
    o = operator.lt if asc else operator.gt
    while o(start, stop):
        yield start
        start += step
