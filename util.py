"""一些工具函数, 绝大部分都不依赖第三方包, 小部分依赖的包也在 doc 中标注了."""

__all__ = (
    'Memoize',
    'clean_textarea',
    'cls_fields',
    'make_accessors',
    'run_shell',
    'temporary_chdir',
    'upload',
    'write_csv',
)

import csv
import os
import warnings
from contextlib import contextmanager
from functools import partialmethod
from inspect import signature
from io import StringIO
from typing import Callable, ContextManager, IO, List, NoReturn, Optional, TYPE_CHECKING, Union

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


def upload(url: str, file: Union[str, IO[str]], file_name: str=None) -> 'Response':
    """上传文件

    file: 可以是一个 str 代表文件路径, 也可以是一个类文件对象, 比如 io.StringIO.

    file_name: 上传的文件名, 如果不指定并且 ``file`` 是 str 则从 ``file`` 中提取,
               如果 ``file`` 不是 str 则必须指定.
    """
    import requests

    if isinstance(file, str):
        file_name = os.path.split(file)[1] if file_name is None else file_name
        file = open(file)
    else:
        if file_name is None:
            raise ValueError('You must specify file_name arg, if file type is str')

    r = requests.post(url=url, files={'file': (file_name, file)})
    return r


def write_csv(header: List[str], rows: List[List[str]], file_path: Optional[str]=None) -> Union[NoReturn, StringIO]:
    """将数据写入 csv

    file_path: 如果不传入此参数, 则会返回一个 StringIO.
    """
    file = StringIO() if file_path is None else open(file_path, 'w')
    csv_f = csv.writer(file)
    csv_f.writerow(header)
    csv_f.writerows(rows)

    if file_path is None:
        file.seek(0)
        return file
    else:
        file.close()
        return


def clean_textarea(value: str, keep_inline_space: bool=True) -> Union[List[str], List[List[str]]]:
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


def make_accessors(cls: type, target_pattern: str, func: Callable, const_owner: type,
                   const_prefix: Optional[str] = None) -> NoReturn:
    """
    1. 新的类方法名由 target_pattern + const_owner 的所有类属性名组成.
    2. 新的类方法具体功能由 func 提供, func 应该有两个参数, 第一个是 self,
       第二个参数值会被设为 const_owner 对应雷属性的值.
    """
    if const_prefix is None:
        len_prefix = 0
        validate = lambda f: not f.startswith('__')
    else:
        len_prefix = len(const_prefix)
        validate = lambda f: not f.startswith(const_prefix)


    for field, value in const_owner.__dict__.items():
        if not validate(field):
            continue

        target_name = target_pattern % field[len_prefix:].lower()
        if target_name in cls.__dict__:
            raise ValueError('field %s is exist' % target_name)
        param_name = list(signature(func).parameters.keys())[-1]
        # 如果用 partial 那么方法就会变成函数, 失去 self 绑定的功能.
        wrapped = partialmethod(func, **{param_name: value})
        setattr(cls, target_name, wrapped)


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
