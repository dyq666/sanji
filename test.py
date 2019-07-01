__all__ = ()

import os

from util import temporary_chdir


def test_temporary_chdir():
    with temporary_chdir('/'):
        assert os.getcwd() == '/'
    assert os.getcwd()[-4:] == 'util'
