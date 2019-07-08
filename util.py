"""一些工具函数, 绝大部分都不依赖第三方包, 小部分依赖的包也在 doc 中标注了."""

__all__ = (
    'Memoize',
    'clean_textarea',
    'cls_fields',
    'run_shell',
    'temporary_chdir',
    'upload',
)

import os
import warnings
from typing import ContextManager, List, NoReturn, Optional, TYPE_CHECKING, Union
from contextlib import contextmanager

if TYPE_CHECKING:
    from requests import Response


def run_shell(context: Optional[dict] = None, plain: bool = False) -> NoReturn:
    """启动预置变量的交互 shell
    Require: ipython
    """
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
    """在 with 环境下修改工作目录"""
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def cls_fields(cls: type) -> dict:
    """返回所有类属性"""
    return { k: v for k, v in cls.__dict__.items() if not k.startswith('__') }


def upload(url: str, file_path: str, file_name: str=None) -> 'Response':
    """上传文件

    file_name: 上传后的文件名, 如果不指定则从 file_path 中提取
    """
    import requests

    file_name = os.path.split(file_path)[1] if file_name is None else file_name

    r = requests.post(
        url=url,
        files={'file': (file_name, open(file_path))}
    )
    return r


def clean_textarea(value: str, keep_inline_space: bool=True) -> Union[List[str], List[List[str]]]:
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


class Memoize:
    """一个缓存属性, 使用方法类似 @property, 区别是被此装饰器包裹的属性只会计算一次."""

    def __init__(self, fget):
        self.fget = fget
        self.cache_key = 'cache_key_' + fget.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self

        if not hasattr(instance, self.cache_key):
            setattr(instance, self.cache_key, self.fget(instance))
        return getattr(instance, self.cache_key)
