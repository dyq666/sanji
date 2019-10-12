__all__ = ()

import os
from tempfile import TemporaryDirectory

import pytest

from util import (
    CaseInsensitiveDict, Memoize, clean_textarea,
    import_object, round_half_up, sequence_grouper, write_csv,
)


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
            """I am foo"""
            return self.id + 100

    assert Foo.foo.__doc__ == 'I am foo'

    f = Foo()

    assert not hasattr(f, 'cache_key_foo')
    assert f.foo == f.__cache_foo == 101

    f.id = 2
    assert f.foo == f.__cache_foo == 101

    # 直接改缓存的属性
    f.__cache_foo = 2
    assert f.foo == f.__cache_foo == 2


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


def test_import_object():
    obj = import_object('util.import_object')
    assert obj == import_object

    with pytest.raises(ImportError):
        # ValueError
        import_object('util')
        # ModuleNotFoundError
        import_object('util1.import_object')
        # Attribute
        import_object('util.U')


def test_round_half_up():
    # 四舍五入, round 是奇进偶舍
    assert round_half_up(10499, -3) == 10000
    assert round_half_up(10500, -3) == 11000
    assert round(10500, -3) == 10000
    assert round_half_up(10501, -3) == 11000

    # 0.155 是无限小数, 0.154999...
    # 因此无论是奇进偶舍还是四舍五入都应该变为 0.16
    assert round(0.155, 2) == 0.15
    assert round_half_up(0.155, 2) == 0.16

    # 0.125 和 0.375 都是有限小数
    # 可以看出奇进偶舍和四舍五入的区别
    assert round(0.125, 2) == 0.12
    assert round(0.375, 2) == 0.38
    assert round_half_up(0.125, 2) == 0.13
    assert round_half_up(0.375, 2) == 0.38


class TestSequenceGrouper:

    @pytest.mark.parametrize('sequence', ([], '', (), b''))
    def test_empty(self, sequence):
        assert list(sequence_grouper(sequence, size=9)) == []

    @pytest.mark.parametrize('sequence', (
        list(range(10)), '世界你好好世界再见见', tuple(range(10)), bytearray(range(10))
    ))
    def test_not_empty(self, sequence):
        assert list(sequence_grouper(sequence, size=9)) == \
            [sequence[:9], sequence[9:10]]
        assert list(sequence_grouper(sequence, size=10)) == [sequence]
        assert list(sequence_grouper(sequence, size=11)) == [sequence]


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
