"""一些工具函数, 绝大部分都不依赖第三方包, 小部分依赖的包也在 doc 中标注了."""

__all__ = (
    'CaseInsensitiveDict',
    'Memoize',
    'Relationship',
    'clean_textarea',
    'cls_fields',
    'get_month_last_datetime',
    'get_number',
    'import_object',
    'is_subclass',
    'make_accessors',
    'round_half_up',
    'run_shell',
    'sequence_grouper',
    'temporary_chdir',
    'upload',
    'write_csv',
    'yearly_ranges',
)

import csv
import math
import os
import warnings
from collections import UserDict
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from functools import partial
from importlib import import_module
from inspect import signature
from io import StringIO
from typing import (
    Any, Callable, ContextManager, IO, Iterable, List,
    NoReturn, Optional, Sequence, Tuple, TYPE_CHECKING, Union,
)

if TYPE_CHECKING:
    from datetime import date
    from requests import Response


class CaseInsensitiveDict(UserDict):

    """
    C: __setitem__
    U: __setitem__
    R: __getitem__, __contains__, get
    D: __delitem__
    """

    def __getitem__(self, key):
        return super().__getitem__(key.lower())

    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)

    def __delitem__(self, key):
        super().__delitem__(key.lower())

    def __contains__(self, key: str):
        return super().__contains__(key.lower())

    def get(self, key, default=None):
        return super().get(key, default)


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


class Relationship:

    """用于 model 中的外键.

    由于公司通常不会使用外键约束, 所以 orm 库提供的相关函数都是无法使用的.

    使用此描述器可以简化描述外键关系的代码量.
    """

    def __init__(self, cls_path, cls_method, instance_field_name):
        self.cls_path = cls_path
        self.cls_method = cls_method
        self.instance_field_name = instance_field_name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        imported_cls = import_object(self.cls_path)
        func = getattr(imported_cls, self.cls_method)
        instance_field_value = getattr(instance, self.instance_field_name)
        return func(instance_field_value)


def clean_textarea(value: str, keep_inline_space: bool = True
                   ) -> Union[List[str], List[List[str]]]:
    rows = [r.strip() for r in value.splitlines() if r and not r.isspace()]
    return rows if keep_inline_space else [r.split() for r in rows]


def cls_fields(cls: type) -> dict:
    """返回所有类属性"""
    return {k: v for k, v in cls.__dict__.items() if not k.startswith('__')}


def get_month_last_datetime(year: int, month: int) -> datetime:
    """本月最后一秒

    Require: pipenv install python-dateutil
    """
    from dateutil.relativedelta import relativedelta
    return (datetime(year, month, 1)
            + relativedelta(months=1)
            - relativedelta(seconds=1))


def get_number(number: Union[int], ndigits: int = 0) -> int:
    """获取某位上的数字

    `ndigits`: 与 `round()` 的参数 `ndigits` 保持一样的逻辑, 0 代表个位, -1 代表十位 ...
    """
    if ndigits > 0:
        raise ValueError('ndigits must <= 0')

    return (number // 10 ** abs(ndigits)) % 10


def import_object(object_path: str) -> Any:
    try:
        dot = object_path.rindex('.')
        module, obj = object_path[:dot], object_path[dot + 1:]
        return getattr(import_module(module), obj)
    # rindex        -> ValueError
    # import_module -> ModuleNotFoundError
    # getattr       -> AttributeError
    except (ValueError, ModuleNotFoundError, AttributeError):
        raise ImportError(f'Cannot import {object_path}')


def is_subclass(sub_cls: type, base_cls: type, is_silent: bool = False
                ) -> bool:
    """当 sub_cls 参数传入的不是 type 类型, issubclass 会 raise TypeError"""
    if not is_silent:
        return issubclass(sub_cls, base_cls)
    try:
        return issubclass(sub_cls, base_cls)
    except TypeError:
        return False


def make_accessors(cls: type, target_pattern: str, func: Callable,
                   const_owner: type, const_prefix: Optional[str] = None
                   ) -> NoReturn:
    """
    1. 将要增加的类方法名由 target_pattern + const_owner 的所有类属性名组成,

       可以用 const_prefix 来指定 const_owner 中的类属性名前缀对类属性进行过滤.

    2. 将要增加的类方法具体功能由 func 提供, func 应该有两个参数, 第一个是 self,

       第二个参数值会被设为 const_owner 对应的类属性的值.
    """
    if const_prefix is None:
        len_prefix = 0
        validate = lambda f: not f.startswith('__')
    else:
        len_prefix = len(const_prefix)
        validate = lambda f: f.startswith(const_prefix)

    arg_names = list(signature(func).parameters.keys())
    if len(arg_names) >= 3:
        raise ValueError('func arg number >= 3')
    param_name = arg_names[1]

    for field, value in const_owner.__dict__.items():
        if not validate(field):
            continue

        target_name = target_pattern % field[len_prefix:].lower()
        if target_name in cls.__dict__:
            raise ValueError('field %s is exist' % target_name)
        wrapped = property(partial(func, **{param_name: value}))
        setattr(cls, target_name, wrapped)


def round_half_up(number: Union[int, float],
                  ndigits: int = 0) -> Union[int, float]:
    """四舍五入.

    `ndigits`: 与 `round()` 的参数 `ndigits` 保持一样的逻辑, 整数代表小数位, 0 代表个位, -1 代表十位 ...

    Require: util.get_number
    """
    if ndigits < 0:
        half_even_result = round(number, ndigits)

        # 如果保留位是偶数, 它的后一位是 5, 并且后面剩下的位都是 0.
        if (get_number(number, ndigits) & 1 == 0
                and get_number(number, ndigits + 1) == 5
                and number % (10 ** abs(ndigits + 1)) == 0):
            half_even_result += 10 ** abs(ndigits)
        return int(half_even_result)

    ndigits = Decimal(str(1 / (10 ** ndigits)))
    return (
        float(Decimal(str(number))
              .quantize(ndigits, rounding=ROUND_HALF_UP))
    )


def run_shell(context: Optional[dict] = None, plain: bool = False) -> NoReturn:
    """启动预置变量的交互 shell

    Require: pipenv install ipython
    """
    if plain:
        import code
        code.interact(local=context)
    else:
        # learn from
        # https://github.com/ei-grad/flask-shell-ipython/blob/master/flask_shell_ipython.py
        try:
            import IPython
            from IPython.terminal.ipapp import load_default_config
            config = load_default_config()
            prompt = 'Preset Vars:\n%s\n' % '\n'.join(
                f'  - {key}' for key in context.keys())
            config.TerminalInteractiveShell.banner1 = prompt
            IPython.start_ipython(config=config, user_ns=context)
        except ImportError:
            warnings.warn('Must install ipython')


def sequence_grouper(sequence: Sequence, size: int) -> Iterable:
    len_ = len(sequence)
    times = math.ceil(len_ / size)
    return (sequence[i * size: (i + 1) * size] for i in range(times))


@contextmanager
def temporary_chdir(path: str) -> ContextManager:
    """在 with 环境下修改工作目录"""
    cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(cwd)


def upload(url: str, file: Union[str, IO[str]],
           file_name: str = None) -> 'Response':
    """上传文件

    Require: pipenv install requests

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
            file_name = 'data.csv'

    r = requests.post(url=url, files={'file': (file_name, file)})
    return r


def write_csv(header: List[str], rows: List[Union[list, dict]],
              file_path: Optional[str] = None) -> Union[NoReturn, StringIO]:
    """将数据写入 csv

    file_path: 如果不传入此参数, 则会返回一个 StringIO.
    """
    assert len(rows), 'Rows cannot empty'

    file = StringIO() if file_path is None else open(file_path, 'w')
    if isinstance(rows[0], dict):
        f_csv = csv.DictWriter(file, header)
        f_csv.writeheader()
        f_csv.writerows(rows)
    elif isinstance(rows[0], list):
        f_csv = csv.writer(file)
        f_csv.writerow(header)
        f_csv.writerows(rows)
    else:
        return

    if file_path is None:
        file.seek(0)
        return file
    else:
        file.close()
        return


def yearly_ranges(begin: Union['date', datetime], end: Union['date', datetime],
                  years: int = 1, find_date: Union['date', datetime] = None
                  ) -> Union[List[Tuple], Tuple, None]:
    """生成的时间范围是左闭右开的.

    Require: pipenv install python-dateutil

    如果不指定 find_date 则会生成如下格式的生成器 (都是左闭右开的):
    [
        (begin,          one_year_later),
        (one_year_later, two_year_later),
        (two_year_later, end)
    ]

    如果指定 find_date, 则从上面生成的范围中找到一个合适的范围, 如果没有则返回 None, 有返回如下结构
    (
        begin, end
    )
    """

    if begin > end:
        raise ValueError('begin time must <= end time')
    if years <= 0:
        raise ValueError('years must >= 1')

    from dateutil.relativedelta import relativedelta

    ranges = []
    while True:
        few_years_later = begin + relativedelta(years=years)
        if few_years_later >= end:
            ranges.append((begin, end))
            break
        ranges.append((begin, few_years_later))
        begin = few_years_later

    if find_date is None:
        return ranges

    if find_date < ranges[0][0] or find_date >= ranges[-1][-1]:
        return
    for begin, end in ranges:
        if find_date < end:
            return begin, end
