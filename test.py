__all__ = ()

import os

import pytest

from util import Memoize, clean_textarea, cls_fields, make_accessors, temporary_chdir, write_csv


def test_temporary_chdir():
    with temporary_chdir('/'):
        assert os.getcwd() == '/'
    assert os.getcwd()[-4:] == 'util'


def test_cls_fields():
    class Foo:
        bar = 1
        _a = 2

        def __init__(self):
            pass

        def foo(self):
            pass


    assert set(dict(cls_fields(Foo)).keys()) == {'bar', 'foo', '_a'}


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


def test_write_csv():
    file = write_csv(['name', 'sex'], [['dyq', 'male'], ['yqd', 'female']])
    assert file.getvalue().replace('\r\n', '\n') == '\n'.join(['name,sex', 'dyq,male', 'yqd,female', ''])


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
    # class
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

    assert Foo(0).is_a and Foo(1).is_b
    assert not hasattr(Foo, 'is_c')
