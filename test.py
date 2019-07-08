__all__ = ()

import os

from util import Memoize, clean_textarea, cls_fields, temporary_chdir, write_csv


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
