__all__ = (
    'CaseInsensitiveDict',
    'Memoize',
    'Relationship',
    'clean_textarea',
    'import_object',
    'make_accessors',
    'round_half_up',
    'sequence_grouper',
    'write_csv',
)

import csv
import math
from collections import UserDict
from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from importlib import import_module
from inspect import signature
from io import StringIO
from typing import (
    Any, Callable, Iterable, List,
    NoReturn, Optional, Sequence, Tuple, Union,
)

Number = Union[int, float]


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


def round_half_up(number: Number, ndigits: int = 0) -> Number:
    """四舍五入.

    ndigits: 与 ``round`` 的参数 ``ndigits`` 保持一样的逻辑:
             > 0 小数位, <= 0 整数位.
    """
    def _get_number(_ndigits: int) -> int:
        return int(str(number)[_ndigits - 1])

    if ndigits <= 0:
        half_even_result = int(round(number, ndigits))

        # 如果保留位是偶数 & 保留位后一位是 5 & 5 后面全是 0, 那么就入
        if all((
            _get_number(ndigits) & 1 == 0,
            _get_number(ndigits + 1) == 5,
            number % (10 ** abs(ndigits + 1)) == 0
        )):
            return half_even_result + 10 ** abs(ndigits)
        return half_even_result

    decimal = Decimal(str(number))
    position = Decimal('0.{}1'.format('0' * (abs(ndigits) - 1)))
    return float(decimal.quantize(position, rounding=ROUND_HALF_UP))


def sequence_grouper(sequence: Sequence, size: int) -> Iterable:
    """按组迭代"""
    times = math.ceil(len(sequence) / size)
    return (sequence[i * size: (i + 1) * size] for i in range(times))


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
