__all__ = (
    'ipython_shell',
    'regular_shell',
)

from typing import NoReturn, Optional


def regular_shell(context: Optional[dict] = None) -> NoReturn:
    """预置变量的常规交互终端"""
    import code
    code.interact(local=context)


def ipython_shell(context: Optional[dict] = None) -> NoReturn:
    """预置变量的ipython 的交互终端"""
    import IPython
    IPython.start_ipython(user_ns=context)
