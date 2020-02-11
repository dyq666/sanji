from datetime import date, datetime, timedelta

import pytest
from dateutil.relativedelta import relativedelta

from util import date_range


@pytest.mark.parametrize('date_cls', (date, datetime))
def test_date_range(date_cls):
    assert list(date_range(date_cls(2019, 1, 1), date_cls(2019, 1, 1))) == []
    assert list(date_range(date_cls(2019, 1, 2), date_cls(2019, 1, 1))) == []
    assert list(date_range(date_cls(2019, 1, 1), date_cls(2019, 1, 1), relativedelta(months=1))) == []
    assert list(date_range(date_cls(2019, 1, 1),
                           date_cls(2019, 1, 1),
                           timedelta(days=-1),
                           asc=False)) == []
    assert list(date_range(date_cls(2019, 1, 1),
                           date_cls(2019, 1, 2),
                           timedelta(days=-1),
                           asc=False)) == []
    assert list(date_range(date_cls(2019, 1, 1),
                           date_cls(2019, 1, 1),
                           relativedelta(months=-1),
                           asc=False)) == []

    assert list(date_range(date_cls(2019, 1, 31),
                           date_cls(2019, 2, 2))) == [date_cls(2019, 1, 31),
                                                      date_cls(2019, 2, 1)]
    assert list(date_range(date_cls(2019, 1, 31),
                           date_cls(2019, 2, 2),
                           timedelta(days=2))) == [date_cls(2019, 1, 31)]
    assert list(date_range(date_cls(2019, 2, 1),
                           date_cls(2019, 1, 30),
                           timedelta(days=-1),
                           asc=False)) == [date_cls(2019, 2, 1),
                                           date_cls(2019, 1, 31)]
    assert list(date_range(date_cls(2019, 2, 2),
                           date_cls(2019, 1, 31),
                           timedelta(days=-2),
                           asc=False)) == [date_cls(2019, 2, 2)]
    assert list(date_range(date_cls(2019, 1, 1),
                           date_cls(2019, 3, 1),
                           relativedelta(months=1))) == [date_cls(2019, 1, 1),
                                                         date_cls(2019, 2, 1)]
    assert list(date_range(date_cls(2019, 3, 1),
                           date_cls(2019, 1, 1),
                           relativedelta(months=-1),
                           asc=False)) == [date_cls(2019, 3, 1),
                                           date_cls(2019, 2, 1)]
