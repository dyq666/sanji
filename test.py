__all__ = ()

import os
from tempfile import TemporaryDirectory

import pytest

from util import (
    Relationship, Memoize, clean_textarea, cls_fields,
    make_accessors, temporary_chdir, write_csv,
)


class User:
    """for test_Relationship"""
    @classmethod
    def get(cls, user_id):
        return user_id


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
        def __init__(self, user_id): self.user_id = user_id

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
    assert clean_textarea(textarea, keep_inline_space=False) == [['1', 'a'], ['2', 'b'], ['3', 'c']]


def test_cls_fields():
    class Foo:
        bar = 1
        _a = 2

        def __init__(self):
            pass

        def foo(self):
            pass


    assert set(dict(cls_fields(Foo)).keys()) == {'bar', 'foo', '_a'}


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
            def _is_status(self, status): pass
            def is_a(self): pass
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


def test_temporary_chdir():
    with temporary_chdir('/'):
        assert os.getcwd() == '/'
    assert os.getcwd()[-4:] == 'util'


# TODO(test upload)


def test_write_csv():
    header = ['name', 'sex']
    rows = [['dyq', 'male'], ['yqd', 'female']]
    csv_content = '\n'.join(['name,sex', 'dyq,male', 'yqd,female', ''])

    file = write_csv(header, rows)
    assert file.getvalue().replace('\r\n', '\n') == csv_content

    # test arg:file_path
    with TemporaryDirectory() as dirname:
        file_path = os.path.join(dirname, 'data.csv')
        write_csv(header, rows, file_path)

        with open(file_path) as f:
            assert f.read() == csv_content
