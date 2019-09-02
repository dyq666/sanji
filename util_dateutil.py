__all__ = (
    'yearly_ranges',
)

from datetime import date, datetime
from typing import List, Tuple, Union


def yearly_ranges(begin: Union[date, datetime], end: Union[date, datetime],
                  years: int = 1, find_date: Union[date, datetime] = None
                  ) -> Union[List[Tuple], Tuple, None]:
    """生成的时间范围是左闭右开的.

    Require: pipenv install python-dateutil

    如果不指定 find_date 则会生成如下格式的生成器 (都是左闭右开的):
    [
        (begin,          one_year_later),
        (one_year_later, two_year_later),
        (two_year_later, end)
    ]

    如果指定 find_date, 则从上面生成的范围中找到一个合适的范围, 如果没有则返回 None, 有返回如下结构
    (
        begin, end
    )
    """

    if begin > end:
        raise ValueError('begin time must <= end time')
    if years <= 0:
        raise ValueError('years must >= 1')

    from dateutil.relativedelta import relativedelta

    ranges = []
    while True:
        few_years_later = begin + relativedelta(years=years)
        if few_years_later >= end:
            ranges.append((begin, end))
            break
        ranges.append((begin, few_years_later))
        begin = few_years_later

    if find_date is None:
        return ranges

    if find_date < ranges[0][0] or find_date >= ranges[-1][-1]:
        return
    for begin, end in ranges:
        if find_date < end:
            return begin, end
