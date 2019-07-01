__all__ = (
    'run_shell',
    'temporary_chdir',
)

import os
import warnings
from typing import NoReturn, Optional, ContextManager
from contextlib import contextmanager


def run_shell(context: Optional[dict] = None, plain: bool = False) -> NoReturn:
    """启动预置变量的交互 shell"""
    if plain:
        import code
        code.interact(local=context)
    else:
        try:
            import IPython
            IPython.start_ipython(user_ns=context)
        except ImportError:
            warnings.warn('Must install ipython')


@contextmanager
def temporary_chdir(path: str) -> ContextManager:
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)
