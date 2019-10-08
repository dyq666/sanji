__all__ = (
    'CaseInsensitiveDict',
    'Memoize',
    'Relationship',
    'clean_textarea',
    'cls_fields',
    'flat_iterable',
    'get_number',
    'import_object',
    'is_subclass',
    'make_accessors',
    'round_half_up',
    'sequence_grouper',
    'temporary_chdir',
    'write_csv',
)

import csv
import math
import os
from collections import UserDict
from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_UP
from functools import partial
from importlib import import_module
from inspect import signature
from itertools import chain
from io import StringIO
from typing import (
    Any, Callable, ContextManager, Iterable, List,
    NoReturn, Optional, Sequence, Tuple, Union,
)


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


def flat_iterable(iterable: Iterable, sequence_cls: Callable = tuple) -> Sequence:
    return sequence_cls(chain(*iterable))


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


def write_csv(header: Tuple[str, ...],
              rows: Union[Tuple[dict, ...], Tuple[list, ...], Tuple[tuple, ...]],
              out_path: Optional[str] = None
              ) -> Union[NoReturn, StringIO]:
    """将数据写入 csv

    header: 标题

    rows: 数据行

    out_path: 不传会返回一个 StringIO, 传则写入此路径.
    """
    if not header or not rows:
        raise ValueError('header or rows should not empty')
    if not isinstance(rows[0], (dict, list, tuple)):
        raise TypeError('type of row item must be dict or tuple or list')

    file = StringIO() if out_path is None else open(out_path, 'w')

    if isinstance(rows[0], dict):
        f_csv = csv.DictWriter(file, header)
        f_csv.writeheader()
        f_csv.writerows(rows)
    else:
        f_csv = csv.writer(file)
        f_csv.writerow(header)
        f_csv.writerows(rows)

    if out_path is None:
        file.seek(0)
        return file
    else:
        file.close()
        return
