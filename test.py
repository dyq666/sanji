__all__ = ()

import os

from util import cls_fields, temporary_chdir


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
