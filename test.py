__all__ = ()

import os
from datetime import date, datetime
from functools import partial
from tempfile import TemporaryDirectory

import pytest

from util import (
    CaseInsensitiveDict, Relationship, Memoize, clean_textarea, cls_fields,
    get_month_last_datetime, get_number, import_object, is_subclass,
    make_accessors, round_half_up, sequence_grouper, temporary_chdir,
    write_csv, yearly_ranges,
)


class User:
    """
    for test_Relationship
        test_import_object
    """

    @classmethod
    def get(cls, user_id):
        return user_id


def test_CaseInsensitiveDict():
    d = CaseInsensitiveDict()
    content_type = 'application/json'

    # __setitem__, __getitem__
    d['Content-Type'] = content_type
    assert d['content-type'] == content_type

    # get
    assert d.get('content-Type') == content_type
    assert d.get('dsa') is None
    assert d.get('dasda', 1) == 1

    # __delitem__, __contains__
    del d['Content-Type']
    assert 'Content-Type' not in d


def test_Memoize():
    class Foo:

        def __init__(self):
            self.id = 1

        @Memoize
        def foo(self):
            return self.id

    f = Foo()

    assert not hasattr(f, 'cache_key_foo')
    assert f.foo == 1
    assert f.cache_key_foo == 1

    f.id = 2
    assert f.foo == 1


def test_Relationship():
    class Book:
        user = Relationship('test.User', 'get', 'user_id')

        def __init__(self, user_id):
            self.user_id = user_id

    assert Book(user_id=1).user == 1


def test_clean_textarea():
    textarea = """
    1

    2
    3

    """
    assert clean_textarea(textarea) == ['1', '2', '3']

    textarea = """
    1 a
    2\t\t b
    \t
    3      c
    """
    assert clean_textarea(textarea, keep_inline_space=False) == \
        [['1', 'a'], ['2', 'b'], ['3', 'c']]


def test_cls_fields():
    class Foo:
        bar = 1
        _a = 2

        def __init__(self):
            pass

        def foo(self):
            pass

    assert set(dict(cls_fields(Foo)).keys()) == {'bar', 'foo', '_a'}


def test_get_month_last_datetime():
    new_datetime = partial(datetime, hour=23, minute=59, second=59)

    # 测试闰年
    # 整除 4, 但不整除 200
    assert get_month_last_datetime(2020, 2) == new_datetime(2020, 2, 29)
    # 整除 4, 且整除 200, 但整除 400
    assert get_month_last_datetime(2000, 2) == new_datetime(2000, 2, 29)

    # 测试第一个月和最后一个月
    assert get_month_last_datetime(2019, 1) == new_datetime(2019, 1, 31)
    assert get_month_last_datetime(2019, 12) == new_datetime(2019, 12, 31)


def test_get_number():
    groups = [
        (14230, [1, 4, 2, 3, 0]),
        (9999, [9, 9, 9, 9]),
    ]
    for i, (number, res) in enumerate(groups):
        assert get_number(number, -i) == res[-(i + 1)]

    with pytest.raises(ValueError):
        get_number(13212, 1)


def test_import_object():
    Cls = import_object('test.User')
    assert hasattr(Cls, 'get')

    with pytest.raises(ImportError):
        import_object('test.U')


def test_is_subclass():
    assert is_subclass(object, object)
    assert not is_subclass(object, type)
    with pytest.raises(TypeError):
        is_subclass(1, object)

    assert is_subclass(object, object, is_silent=True)
    assert not is_subclass(object, type, is_silent=True)
    assert not is_subclass(1, object, is_silent=True)


def test_make_accessor():
    class Foo:
        def __init__(self, status):
            self.status = status

        def _is_status(self, status) -> bool:
            return status == self.status

    class Status:
        A = 0
        B = 1

    make_accessors(Foo, 'is_%s', Foo._is_status, Status)

    assert Foo(0).is_a and Foo(1).is_b
    assert not Foo(0).is_b and not Foo(1).is_a

    # 如果新生成的方法名与现有的重复就会报错.
    with pytest.raises(ValueError):
        class Foo2:
            def _is_status(self, status):
                pass

            def is_a(self):
                pass

        make_accessors(Foo, 'is_%s', Foo2._is_status, Status)

    # 测试 const_prefix
    class Foo3:
        def __init__(self, status):
            self.status = status

        def _is_status(self, status) -> bool:
            return status == self.status

    class Status2:
        S_A = 0
        S_B = 1
        A_C = 2

    make_accessors(Foo3, 'is_%s', Foo3._is_status, Status2, const_prefix='S_')

    assert Foo3(0).is_a and Foo3(1).is_b
    assert hasattr(Foo3, 'is_a')
    assert not hasattr(Foo3, 'is_c')


def test_round_half_up():
    assert round_half_up(10499, -3) == 10000
    assert round_half_up(10510, -3) == 11000

    assert round(10500, -3) == 10000
    assert round_half_up(10500, -3) == 11000

    assert round(0.155, 2) == 0.15
    assert round_half_up(0.155, 2) == 0.16


# TODO test run_shell


class TestSequenceGrouper:

    @pytest.mark.parametrize('sequence', ([], ''))
    def test_empty(self, sequence):
        assert list(sequence_grouper(sequence, size=9)) == []

    @pytest.mark.parametrize('sequence', (
        list(range(10)), 'abcdefghij', '世界你好好世界再见见',
    ))
    def test_not_empty(self, sequence):
        assert list(sequence_grouper(sequence, size=9)) == \
            [sequence[:9], sequence[9:10]]
        assert list(sequence_grouper(sequence, size=10)) == [sequence]
        assert list(sequence_grouper(sequence, size=11)) == [sequence]


def test_temporary_chdir():
    with temporary_chdir('/'):
        assert os.getcwd() == '/'
    assert os.getcwd()[-4:] == 'util'


# TODO test upload


class TestWriteCSV:

    header = ('name', 'sex')
    rows = (('father', 'male'), ('mother', 'female'))
    content = 'name,sex\nfather,male\nmother,female\n'

    def test_expected_exceptions(self):
        with pytest.raises(ValueError):
            write_csv((), ())
        with pytest.raises(TypeError):
            write_csv(('1',), ({1}))

    def test_row_item_type(self):
        rows_fixtures = (
            self.rows,
            tuple(list(row) for row in self.rows),
            tuple({header: datum for header, datum in zip(self.header, row)}
                  for row in self.rows),
        )
        for rows in rows_fixtures:
            file = write_csv(self.header, rows)
            assert file.getvalue().replace('\r\n', '\n') == self.content

    def test_out_path_arg(self):
        header = self.header
        rows = self.rows
        csv_content = self.content

        file = write_csv(header, rows)
        assert file.getvalue().replace('\r\n', '\n') == csv_content

        with TemporaryDirectory() as dirname:
            file_path = os.path.join(dirname, 'data.csv')
            write_csv(header, rows, file_path)

            with open(file_path) as f:
                assert f.read() == csv_content


@pytest.mark.parametrize('date_cls', [date, datetime])
def test_yearly_ranges(date_cls):
    with pytest.raises(ValueError):
        yearly_ranges(date_cls(2019, 1, 2), date_cls(2019, 1, 1))
    with pytest.raises(ValueError):
        yearly_ranges(date_cls(2019, 1, 1), date_cls(2019, 1, 2), 0)

    # 测试开始和结束时间相同
    assert yearly_ranges(date_cls(2019, 1, 2), date_cls(2019, 1, 2)) == [
        (date_cls(2019, 1, 2), date_cls(2019, 1, 2))
    ]

    # 测试结束比开始多一年
    assert yearly_ranges(date_cls(2019, 1, 2), date_cls(2020, 1, 2)) == [
        (date_cls(2019, 1, 2), date_cls(2020, 1, 2))
    ]

    # 测试结束比开始多一年 + 一天
    assert yearly_ranges(date_cls(2019, 1, 2), date_cls(2020, 1, 3)) == [
        (date_cls(2019, 1, 2), date_cls(2020, 1, 2)),
        (date_cls(2020, 1, 2), date_cls(2020, 1, 3)),
    ]

    # 测试结束比开始多一年 - -天
    assert yearly_ranges(date_cls(2019, 1, 2), date_cls(2020, 1, 1)) == [
        (date_cls(2019, 1, 2), date_cls(2020, 1, 1))
    ]

    new_yearly_ranges = partial(yearly_ranges,
                                date_cls(2019, 1, 2), date_cls(2022, 3, 2))

    assert new_yearly_ranges(find_date=date_cls(2019, 1, 1)) is None
    assert new_yearly_ranges(find_date=date_cls(2022, 3, 2)) is None
    assert new_yearly_ranges(find_date=date_cls(2022, 3, 3)) is None

    assert new_yearly_ranges(find_date=date_cls(2019, 1, 2)) == \
        (date_cls(2019, 1, 2), date_cls(2020, 1, 2))
    assert new_yearly_ranges(find_date=date_cls(2020, 1, 1)) == \
        (date_cls(2019, 1, 2), date_cls(2020, 1, 2))
    assert new_yearly_ranges(find_date=date_cls(2022, 3, 1)) == \
        (date_cls(2022, 1, 2), date_cls(2022, 3, 2))
